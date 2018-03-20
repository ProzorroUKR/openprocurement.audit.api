from openprocurement.audit.api.traversal import factory
from functools import partial
from cornice.resource import resource
from schematics.exceptions import ModelValidationError
from openprocurement.api.models import Revision
from openprocurement.api.utils import (
    update_logging_context, context_unpack, get_revision_changes, get_now,
    apply_data_patch, error_handler
)
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
    patch = get_revision_changes(monitor.serialize("plain"), request.validated['monitor_src'])
    if patch:
        monitor.revisions.append(
            Revision({'author': request.authenticated_userid, 'changes': patch, 'rev': monitor.rev})
        )
        old_date_modified = monitor.dateModified
        monitor.dateModified = get_now()
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
                'Saved monitor {}: dateModified {} -> {}'.format(
                    monitor.id, old_date_modified and old_date_modified.isoformat(),
                    monitor.dateModified.isoformat()
                ),
                extra=context_unpack(request, {'MESSAGE_ID': 'save_plan'}, {'PLAN_REV': monitor.rev})
            )
            return True


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_monitor(request)


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
    monitor_id = request.matchdict['monitor_id']
    return extract_monitor_adapter(request, monitor_id)