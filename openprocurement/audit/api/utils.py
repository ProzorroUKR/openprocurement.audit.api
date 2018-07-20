from couchdb import ResourceConflict
from datetime import timedelta
from gevent import sleep
from openprocurement.api.constants import TZ

from openprocurement.audit.api.traversal import factory
from functools import partial
from cornice.resource import resource
from openprocurement.tender.core.utils import calculate_business_date as calculate_business_date_base
from schematics.exceptions import ModelValidationError
from openprocurement.api.models import Revision, Period
from openprocurement.api.utils import (
    update_logging_context, context_unpack, get_revision_changes,
    apply_data_patch, error_handler, generate_id, get_now,
    check_document, update_document_url
)
from openprocurement.audit.api.models import Monitoring
from pkg_resources import get_distribution
from logging import getLogger
from re import compile

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)

op_resource = partial(resource, error_handler=error_handler, factory=factory)

ACCELERATOR_RE = compile(r'accelerator=(?P<accelerator>\d+)')


class APIResource(object):

    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.db = request.registry.db
        self.server_id = request.registry.server_id
        self.server = request.registry.couchdb_server
        self.update_after = request.registry.update_after
        self.LOGGER = getLogger(type(self).__module__)


def monitoring_serialize(request, monitoring_data, fields):
    monitoring = request.monitoring_from_data(monitoring_data)
    monitoring.__parent__ = request.context
    return {i: j for i, j in monitoring.serialize('view').items() if i in fields}


def save_monitoring(request, date_modified=None):
    monitoring = request.validated['monitoring']
    patch = get_revision_changes(request.validated['monitoring_src'], monitoring.serialize('plain'))
    if patch:
        add_revision(request, monitoring, patch)

        old_date_modified = monitoring.dateModified
        monitoring.dateModified = date_modified or get_now()
        try:
            monitoring.store(request.registry.db)
        except ModelValidationError, e:  # pragma: no cover
            for i in e.message:
                request.errors.add('body', i, e.message[i])
            request.errors.status = 422
        except Exception, e:  # pragma: no cover
            request.errors.add('body', 'data', str(e))
        else:
            LOGGER.info(
                'Saved monitoring {}: dateModified {} -> {}'.format(
                    monitoring.id,
                    old_date_modified and old_date_modified.isoformat(),
                    monitoring.dateModified.isoformat()
                ),
                extra=context_unpack(request, {'MESSAGE_ID': 'save_monitoring'})
            )
            return True


def apply_patch(request, data=None, save=True, src=None, date_modified=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_monitoring(request, date_modified=date_modified)


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
    if 'monitoring' in request.validated:
        params['MONITOR_REV'] = request.validated['monitoring'].rev
        params['MONITOR_ID'] = request.validated['monitoring'].id
    update_logging_context(request, params)


def monitoring_from_data(request, data):
    return Monitoring(data)


def extract_monitoring_adapter(request, monitoring_id):
    db = request.registry.db
    doc = db.get(monitoring_id)
    if doc is None or doc.get('doc_type') != 'Monitoring':
        request.errors.add('url', 'monitoring_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)

    return request.monitoring_from_data(doc)


def extract_monitoring(request):
    monitoring_id = request.matchdict.get('monitoring_id')
    return extract_monitoring_adapter(request, monitoring_id) if monitoring_id else None


def generate_monitoring_id(ctime, db, server_id=''):
    """ Generate ID for new monitoring in format "UA-M-YYYY-MM-DD-NNNNNN" + ["-server_id"]
        YYYY - year, MM - month (start with 1), DD - day, NNNNNN - sequence number per 1 day
        and save monitorings count per day in database document with _id = "monitoringID" 
        as { key, value } = { "2015-12-03": 2 }
    :param ctime: system date-time
    :param db: couchdb database object
    :param server_id: server mark (for claster mode)
    :return: planID in "UA-M-2015-05-08-000005"
    """
    key = ctime.date().isoformat()
    monitoring_id_doc = 'monitoringID_' + server_id if server_id else 'monitoringID'
    while True:
        try:
            monitoring_id = db.get(monitoring_id_doc, {'_id': monitoring_id_doc})
            index = monitoring_id.get(key, 1)
            monitoring_id[key] = index + 1
            db.save(monitoring_id)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return 'UA-M-{:04}-{:02}-{:02}-{:06}{}'.format(
        ctime.year, ctime.month, ctime.day, index, server_id and '-' + server_id)

def generate_period(date, delta, accelerator=None):
    period = Period()
    period.startDate = date
    period.endDate = calculate_business_date(date, delta, accelerator, True)
    return period


def set_ownership(data, request, fieldname='owner'):
    for item in data if isinstance(data, list) else [data]:
        setattr(item, fieldname, request.authenticated_userid)
        setattr(item, '{}_token'.format(fieldname), generate_id())


def set_author(data, request, fieldname='author'):
    for item in data if isinstance(data, list) else [data]:
        setattr(item, fieldname, get_monitoring_role(request.authenticated_role))


def get_monitoring_role(role):
    return 'monitoring_owner' if role == 'sas' else 'tender_owner'


def get_monitoring_accelerator(context):
    if context and 'monitoringDetails' in context and context['monitoringDetails']:
        re_obj = ACCELERATOR_RE.search(context['monitoringDetails'])
        if re_obj and 'accelerator' in re_obj.groupdict():
            try:
                return int(re_obj.groupdict()['accelerator'])
            except ValueError:
                pass
    return 0


def calculate_business_date(date_obj, timedelta_obj, accelerator=None, working_days=False):
    if accelerator:
        return date_obj + (timedelta_obj / accelerator)
    return calculate_business_date_base(date_obj, timedelta_obj, working_days=working_days)


def get_access_token(request):
    """
    Find access token in request in next order:
     - acc_token query param
     - X-Access-Token header
     - access.token body value (for POST, PUT, PATCH and application/json content type)
     
    Raise ValueError if no token provided
    """
    token = request.params.get('acc_token') or request.headers.get('X-Access-Token')
    if token:
        return token
    elif request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
        try:
            return isinstance(request.json_body, dict) and request.json_body.get('access', {})['token']
        except (ValueError, KeyError):
            pass
    raise ValueError('No access token was provided in request.')


def upload_objects_documents(request, obj, key='body'):
    for document in getattr(obj, 'documents', []):
        check_document(request, document, key)
        document_route = request.matched_route.name
        update_document_url(request, document, document_route, {})
