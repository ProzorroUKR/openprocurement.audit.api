from logging import getLogger
from cornice.resource import resource
from functools import partial

from openprocurement.audit.api.mask import mask_object_data
from openprocurement.audit.api.utils import (
    get_revision_changes,
    apply_data_patch,
    error_handler,
    update_logging_context,
    context_unpack,
    handle_store_exceptions,
    append_revision,
    raise_operation_error,
)
from openprocurement.audit.inspection.mask import INSPECTION_MASK_MAPPING
from openprocurement.audit.inspection.models import Inspection
from openprocurement.audit.inspection.traversal import factory
from openprocurement.audit.api.context import get_now

LOGGER = getLogger(__package__)


op_resource = partial(resource, error_handler=error_handler, factory=factory)


def save_inspection(request, modified: bool = True, insert: bool = False) -> bool:
    inspection = request.validated["inspection"]

    patch = get_revision_changes(inspection.serialize("plain"), request.validated["inspection_src"])
    if patch:
        now = get_now()

        append_revision(request, inspection, patch)
        old_date_modified = inspection.get("dateModified", now.isoformat())
        with handle_store_exceptions(request):
            request.registry.mongodb.inspection.save(
                inspection,
                insert=insert,
                modified=modified,
            )
            LOGGER.info(
                "Saved inspection {}: dateModified {} -> {}".format(
                    inspection.id,
                    old_date_modified,
                    inspection.dateModified.isoformat()
                ),
                extra=context_unpack(request, {"MESSAGE_ID": "save_inspection"}, {"RESULT": inspection["_rev"]}),
            )
            return True
    return False


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_inspection(request)


def generate_inspection_id(request):
    ctime = get_now().date()
    index_key = "inspection_{}".format(ctime.isoformat())
    index = request.registry.mongodb.get_next_sequence_value(index_key)
    return 'UA-I-{:04}-{:02}-{:02}-{:06}'.format(ctime.year, ctime.month, ctime.day, index)


def set_logging_context(event):
    request = event.request
    params = {}
    if 'inspection' in request.validated:
        params['INSPECTION_REV'] = request.validated['inspection'].rev
        params['INSPECTION_ID'] = request.validated['inspection'].id
    update_logging_context(request, params)


def extract_inspection(request):
    key = "inspection_id"
    uid = request.matchdict.get(key)
    if uid:
        doc = request.registry.mongodb.inspection.get(uid)
        if doc is None:
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404
            raise error_handler(request.errors)
        return request.inspection_from_data(doc)


def inspection_serialize(request, data, fields):
    obj = request.inspection_from_data(data, raise_error=False)
    obj.__parent__ = request.context
    return {i: j for i, j in obj.serialize("view").items() if i in fields}


def inspection_from_data(request, data, **_):
    if request.method == 'GET':
        mask_object_data(request, data, mask_mapping=INSPECTION_MASK_MAPPING)
    return Inspection(data)


def extract_restricted_config_from_monitoring(request):
    for monitoring_id in request.validated['inspection'].monitoring_ids:
        monitoring = request.registry.mongodb.monitoring.get(monitoring_id)
        if not monitoring:
            raise_operation_error(request, f'Monitoring {monitoring_id} not found', status=404)
        if monitoring["restricted"]:
            return True
    return False
