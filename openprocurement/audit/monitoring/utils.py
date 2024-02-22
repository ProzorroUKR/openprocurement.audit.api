from cornice.resource import resource
from functools import partial
from logging import getLogger
from re import compile
from datetime import timedelta
from dateorro import calc_datetime, calc_normalized_datetime, calc_working_datetime
from openprocurement.audit.api.constants import TZ, WORKING_DAYS
from openprocurement.audit.api.utils import (
    update_logging_context, context_unpack, get_revision_changes,
    apply_data_patch, error_handler, generate_id,
    check_document, update_document_url,
    append_revision,
    handle_store_exceptions,
    raise_operation_error,
)
from openprocurement.audit.monitoring.mask import MONITORING_MASK_MAPPING
from openprocurement.audit.monitoring.models import Period, Monitoring
from openprocurement.audit.api.models import Revision
from openprocurement.audit.api.mask import mask_object_data
from openprocurement.audit.api.mask_deprecated import mask_object_data_deprecated
from openprocurement.audit.api.context import get_now
from openprocurement.audit.monitoring.traversal import factory

from openprocurement_client.resources.tenders import TendersClient
from openprocurement_client.exceptions import ResourceError

LOGGER = getLogger(__package__)
ACCELERATOR_RE = compile(r'accelerator=(?P<accelerator>\d+)')

op_resource = partial(resource, error_handler=error_handler, factory=factory)


def monitoring_serialize(request, data, fields):
    monitoring = request.monitoring_from_data(data)
    monitoring.__parent__ = request.context
    return {i: j for i, j in monitoring.serialize('view').items()
            if i in fields}


def save_monitoring(request, modified: bool = True, insert: bool = False, update_context_date=False) -> bool:
    monitoring = request.validated["monitoring"]
    patch = get_revision_changes(monitoring.serialize("plain"), request.validated["monitoring_src"])
    if patch:
        now = get_now()
        append_revision(request, monitoring, patch)
        old_date_modified = monitoring.get("dateModified", now.isoformat())
        if update_context_date and "dateModified" in request.context:
            request.context.dateModified = now

        with handle_store_exceptions(request):
            monitoring.validate()  # it had been called before in couchdb-schematics; some validations rely on it
            request.registry.mongodb.monitoring.save(
                monitoring,
                insert=insert,
                modified=modified,
            )
            LOGGER.info(
                "Saved monitoring {}: dateModified {} -> {}".format(
                    monitoring.id,
                    old_date_modified,
                    monitoring.dateModified.isoformat()
                ),
                extra=context_unpack(request, {"MESSAGE_ID": "save_monitoring"}, {"RESULT": monitoring["_rev"]}),
            )
            return True
    return False


def apply_patch(request, data=None, save=True, src=None, update_context_date=False):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_monitoring(request, update_context_date=update_context_date)


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
    # wartime measures
    if request.method == 'GET':
        mask_object_data_deprecated(request, data)
        mask_object_data(request, data, mask_mapping=MONITORING_MASK_MAPPING)
    return Monitoring(data)


def extract_monitoring_adapter(request, monitoring_id):
    data = request.registry.mongodb.monitoring.get(monitoring_id)
    if data is None:
        request.errors.add('url', 'monitoring_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)
    return request.monitoring_from_data(data)


def extract_monitoring(request):
    monitoring_id = request.matchdict.get('monitoring_id')
    return extract_monitoring_adapter(request, monitoring_id) if monitoring_id else None


def extract_restricted_config_from_tender(request):
    try:
        response = TendersClient(
            request.registry.api_token,
            host_url=request.registry.api_server,
            api_version=request.registry.api_version,
        ).get_tender(request.validated['monitoring'].tender_id)
    except ResourceError as e:
        if e.status_code == 404:
            raise_operation_error(
                request,
                'Tender {} not found'.format(request.validated['monitoring'].tender_id),
                status=404,
            )
        else:
            raise_operation_error(request, 'Unsuccessful tender request', status=e.status_code)
    return response.get('config', {}).get('restricted', False)


def generate_monitoring_id(request):
    ctime = get_now().date()
    index_key = "monitoring_{}".format(ctime.isoformat())
    index = request.registry.mongodb.get_next_sequence_value(index_key)
    return 'UA-M-{:04}-{:02}-{:02}-{:06}'.format(ctime.year, ctime.month, ctime.day, index)


def generate_period(date, delta, accelerator=None):
    period = Period()
    period.startDate = date
    period.endDate = calculate_normalized_business_date(date, delta, accelerator)
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
            return int(re_obj.groupdict()['accelerator'])
    return 0


def calculate_normalized_business_date(date_obj, timedelta_obj, accelerator=None):
    if accelerator:
        return calc_datetime(date_obj, timedelta_obj, accelerator)
    normalized_date = calc_normalized_datetime(date_obj, ceil=timedelta_obj > timedelta())
    return calc_working_datetime(normalized_date, timedelta_obj, midnight=True, calendar=WORKING_DAYS)


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
