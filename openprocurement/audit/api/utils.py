from couchdb import ResourceConflict
from gevent import sleep
from openprocurement.audit.api.constraints import MONITORING_TIME
from openprocurement.audit.api.traversal import factory
from functools import partial
from cornice.resource import resource
from openprocurement.tender.core.utils import calculate_business_date
from schematics.exceptions import ModelValidationError
from openprocurement.api.models import Revision, Period
from openprocurement.api.utils import (
    update_logging_context, context_unpack, get_revision_changes,
    apply_data_patch, error_handler, generate_id)
from openprocurement.audit.api.models import Monitor
from pkg_resources import get_distribution
from logging import getLogger

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)

op_resource = partial(resource, error_handler=error_handler, factory=factory)


class APIResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.db = request.registry.db
        self.server_id = request.registry.server_id
        self.server = request.registry.couchdb_server
        self.update_after = request.registry.update_after
        self.LOGGER = getLogger(type(self).__module__)


def monitor_serialize(request, monitor_data, fields):
    monitor = request.monitor_from_data(monitor_data, raise_error=False)
    monitor.__parent__ = request.context
    return {i: j for i, j in monitor.serialize("view").items() if i in fields}


def save_monitor(request):
    monitor = request.validated['monitor']
    patch = get_revision_changes(request.validated['monitor_src'], monitor.serialize("plain"))
    if patch:
        add_revision(request, monitor, patch)
        try:
            monitor.store(request.registry.db)
        except ModelValidationError, e:  # pragma: no cover
            for i in e.message:
                request.errors.add('body', i, e.message[i])
            request.errors.status = 422
        except Exception, e:  # pragma: no cover
            request.errors.add('body', 'data', str(e))
        else:
            LOGGER.info(
                'Saved monitor {}'.format(monitor.id),
                extra=context_unpack(request, {'MESSAGE_ID': 'save_monitor'})
            )
            return True


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_monitor(request)


def add_revision(request, item, changes):
    revision_data = {
        'author': request.authenticated_userid,
        'changes': changes,
        'rev': item.rev
    }
    item.revisions.append(Revision(revision_data))


def set_logging_context(event):
    request = event.request
    params = {}
    if 'monitor' in request.validated:
        params['MONITOR_REV'] = request.validated['monitor'].rev
        params['MONITOR_ID'] = request.validated['monitor'].id
    update_logging_context(request, params)


def monitor_from_data(request, data, raise_error=True, create=True):
    if create:
        return Monitor(data)
    return Monitor


def extract_monitor_adapter(request, monitor_id):
    db = request.registry.db
    doc = db.get(monitor_id)
    if doc is not None and doc.get('doc_type') == 'monitor':
        request.errors.add('url', 'monitor_id', 'Archived')
        request.errors.status = 410
        raise error_handler(request.errors)
    elif doc is None or doc.get('doc_type') != 'Monitor':
        request.errors.add('url', 'monitor_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)

    return request.monitor_from_data(doc)


def extract_monitor(request):
    monitor_id = request.matchdict.get('monitor_id')
    return extract_monitor_adapter(request, monitor_id) if monitor_id else None


def generate_monitor_id(ctime, db, server_id=''):
    """ Generate ID for new monitor in format "UA-M-YYYY-MM-DD-NNNNNN" + ["-server_id"]
        YYYY - year, MM - month (start with 1), DD - day, NNNNNN - sequence number per 1 day
        and save monitors count per day in database document with _id = "monitorID" 
        as { key, value } = { "2015-12-03": 2 }
    :param ctime: system date-time
    :param db: couchdb database object
    :param server_id: server mark (for claster mode)
    :return: planID in "UA-M-2015-05-08-000005"
    """
    key = ctime.date().isoformat()
    monitor_id_doc = 'monitorID_' + server_id if server_id else 'monitorID'
    while True:
        try:
            monitor_id = db.get(monitor_id_doc, {'_id': monitor_id_doc})
            index = monitor_id.get(key, 1)
            monitor_id[key] = index + 1
            db.save(monitor_id)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return 'UA-M-{:04}-{:02}-{:02}-{:06}{}'.format(
        ctime.year, ctime.month, ctime.day, index, server_id and '-' + server_id)

def generate_monitoring_period(date):
    period = Period()
    period.startDate = date
    period.endDate = calculate_business_date(date, MONITORING_TIME, working_days=True)
    return period


def set_documents_of_type(data, of_type):
    for item in data if isinstance(data, list) else [data]:
        item.documentOf = of_type


def set_ownership(data, request, fieldname='owner'):
    for item in data if isinstance(data, list) else [data]:
        if not item.get(fieldname):
            setattr(item, fieldname, request.authenticated_userid)
        setattr(item, '{}_token'.format(fieldname), generate_id())
