# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context, raise_operation_error, error_handler, forbidden
from openprocurement.api.validation import validate_data
from restkit import ResourceNotFound
from hashlib import sha512

from openprocurement_client.client import TendersClient
from openprocurement.audit.api.models import Monitor, Dialogue


def validate_monitor_data(request):
    update_logging_context(request, {'MONITOR_ID': '__new__'})
    return validate_data(request, Monitor)


def validate_patch_monitor_data(request):
    result = validate_data(request, Monitor, partial=True)

    # check sent data that is not allowed in current status
    # acceptable fields are set in Monitor.Options.roles: edit_draft, edit_active, etc
    provided = set(request.validated['json_data'].keys())
    allowed = set(request.validated['data'].keys())
    difference = provided - allowed
    if difference:
        for i in difference:
            request.errors.add('body', i, "This field isn't expected in the {} status".format(
                request.validated["monitor"]["status"]))
        request.errors.status = 422
        raise error_handler(request.errors)

    return result


def validate_patch_monitor_status(request):
    status = request.validated['json_data'].get("status")
    if status is not None and status != request.context.status:
        function_name = "_validate_patch_monitor_status_{}_to_{}".format(request.context.status, status)
        try:
            func = globals()[function_name]
        except KeyError:
            request.errors.add(
                'body', 'status',
                "Status update from '{}' to '{}' is not allowed.".format(request.context.status, status)
            )
            request.errors.status = 422
            raise error_handler(request.errors)
        else:
            return func(request)


def _validate_patch_monitor_status_draft_to_active(request):
    if not request.validated.get("data", {}).get('decision'):
        request.errors.status = 422
        request.errors.add('body', 'decision', 'This field is required.')
        raise error_handler(request.errors)


def validate_dialogue_data(request):
    update_logging_context(request, {'DIALOGUE_ID': '__new__'})
    return validate_data(request, Dialogue)


def validate_patch_dialogue_data(request):
    return validate_data(request, Dialogue, partial=True)


def validate_patch_dialogue_allowed(request):
    owner = request.validated['dialogue']['author']
    if request.authenticated_userid == owner:
        raise_operation_error(request, 'Can\'t edit dialogue')


def validate_document_decision_upload_allowed(request):
    status_current = request.validated['monitor'].status
    if status_current != 'draft':
        raise_operation_error(request, 'Can\'t add document in current {} monitor status'.format(status_current))


def validate_document_conclusion_upload_allowed(request):
    status_current = request.validated['monitor'].status
    if status_current != 'active':
        raise_operation_error(request, 'Can\'t add document in current {} monitor status'.format(status_current))


def validate_credentials_generate(request):
    client = TendersClient(
        request.registry.api_token,
        host_url=request.registry.api_server,
        api_version=request.registry.api_version,
    )
    try:
        response = client.extract_credentials(request.validated['monitor'].tender_id)
        if sha512(request.params.get('acc_token')).hexdigest() != response['data']['tender_token']:
            raise forbidden(request)
    except ResourceNotFound:
        raise_operation_error(request, "Tender {} not found".format(request.validated['monitor'].tender_id))
