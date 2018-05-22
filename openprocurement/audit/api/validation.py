# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context, raise_operation_error, error_handler, forbidden, get_now
from openprocurement.api.validation import validate_data
from restkit import ResourceNotFound
from hashlib import sha512

from openprocurement_client.client import TendersClient
from openprocurement.audit.api.models import Monitoring, Dialogue, EliminationReport, Party


def validate_monitoring_data(request):
    update_logging_context(request, {'MONITOR_ID': '__new__'})
    return validate_data(request, Monitoring)


def validate_patch_monitoring_data(request):
    data = validate_data(request, Monitoring, partial=True)

    # check sent data that is not allowed in current status
    # acceptable fields are set in Monitor.Options.roles: edit_draft, edit_active, etc
    provided = set(request.validated['json_data'].keys())
    allowed = set(request.validated['data'].keys())
    difference = provided - allowed
    if difference:
        for i in difference:
            request.errors.add('body', i, 'This field cannot be updated in the {} status'.format(
                request.validated['monitoring']['status']))
        request.errors.status = 422
        raise error_handler(request.errors)

    return data


def validate_patch_monitoring_status(request):
    status = request.validated['json_data'].get('status')
    if status is not None and status != request.context.status:
        function_name = '_validate_patch_monitoring_status_{}_to_{}'.format(request.context.status, status)
        try:
            func = globals()[function_name]
        except KeyError:
            request.errors.add(
                'body', 'status',
                'Status update from "{}" to "{}" is not allowed.'.format(request.context.status, status)
            )
            request.errors.status = 422
            raise error_handler(request.errors)
        else:
            return func(request)


def _validate_patch_monitoring_status_draft_to_active(request):
    if not request.validated.get('data', {}).get('decision'):
        request.errors.status = 422
        request.errors.add('body', 'decision', 'This field is required.')
        raise error_handler(request.errors)


def _validate_patch_monitoring_status_active_to_addressed(request):
    _validate_patch_monitoring_status_active_to_addressed_or_declined(request)
    if not request.validated.get('data', {}).get('conclusion').get('violationOccurred'):
        raise_operation_error(request, 'Can\'t set addressed status to monitoring if no violation occurred')


def _validate_patch_monitoring_status_active_to_declined(request):
    _validate_patch_monitoring_status_active_to_addressed_or_declined(request)
    if request.validated.get('data', {}).get('conclusion').get('violationOccurred'):
        raise_operation_error(request, 'Can\'t set declined status to monitoring if violation occurred')


def _validate_patch_monitoring_status_active_to_addressed_or_declined(request):
    if not request.validated.get('data', {}).get('conclusion'):
        request.errors.status = 422
        request.errors.add('body', 'conclusion', 'This field is required.')
        raise error_handler(request.errors)


def _validate_patch_monitoring_status_addressed_to_completed(request):
    monitoring = request.validated['monitoring']
    if not get_now() > monitoring.eliminationPeriod.endDate:
        raise_operation_error(request, 'Can\'t change status to completed before elimination period ends.')
    if not request.validated.get('data', {}).get('eliminationResolution'):
        request.errors.status = 422
        request.errors.add('body', 'eliminationResolution', 'This field is required.')

def _validate_patch_monitoring_status_declined_to_closed(request):
    monitoring = request.validated['monitoring']
    if not get_now() > monitoring.eliminationPeriod.endDate:
        raise_operation_error(request, 'Can\'t change status to closed before elimination period ends.')

def _validate_patch_monitoring_status_active_to_stopped(request):
    _validate_patch_monitoring_status_to_stopped_or_cancelled(request)


def _validate_patch_monitoring_status_addressed_to_stopped(request):
    _validate_patch_monitoring_status_to_stopped_or_cancelled(request)


def _validate_patch_monitoring_status_declined_to_stopped(request):
    _validate_patch_monitoring_status_to_stopped_or_cancelled(request)


def _validate_patch_monitoring_status_draft_to_cancelled(request):
    _validate_patch_monitoring_status_to_stopped_or_cancelled(request)


def _validate_patch_monitoring_status_to_stopped_or_cancelled(request):
    if not request.validated.get('data', {}).get('cancellation'):
        request.errors.status = 422
        request.errors.add('body', 'stopping', 'This field is required.')
        raise error_handler(request.errors)


def validate_dialogue_data(request):
    update_logging_context(request, {'DIALOGUE_ID': '__new__'})
    return validate_data(request, Dialogue)


def validate_patch_dialogue_data(request):
    return validate_data(request, Dialogue, partial=True)


def validate_party_data(request):
    update_logging_context(request, {'PARTY_ID': '__new__'})
    return validate_data(request, Party)


def validate_patch_party_data(request):
    return validate_data(request, Party, partial=True)


def validate_post_dialogue_allowed(request):
    monitoring = request.validated['monitoring']
    status_current = monitoring.status
    if status_current in ('addressed', 'declined'):
        if request.authenticated_userid != request.validated['monitoring'].tender_owner:
            raise forbidden(request)
        if sum(dialogue.dialogueOf == 'conclusion' for dialogue in monitoring.dialogues):
            raise_operation_error(request, 'Can\'t add more than one conclusion dialogue')
    elif status_current not in ('active',):
        raise_operation_error(request, 'Can\'t add dialogue in current {} monitoring status'.format(status_current))


def validate_patch_dialogue_allowed(request):
    dialogue = request.validated['dialogue']
    owner = dialogue['author']
    if request.authenticated_userid == owner:
        raise forbidden(request)
    monitoring = request.validated['monitoring']
    status_current = monitoring.status
    if dialogue.dialogueOf == 'conclusion' and status_current not in ('addressed', 'declined'):
        raise_operation_error(request, 'Can\'t edit conclusion dialogue in current {} monitoring status'.format(
            status_current))
    elif dialogue.dialogueOf == 'decision' and status_current not in ('active',):
        raise_operation_error(request, 'Can\'t edit decision dialogue in current {} monitoring status'.format(
            status_current))


def validate_document_decision_upload_allowed(request):
    status_current = request.validated['monitoring'].status
    if status_current != 'draft':
        raise_operation_error(request, 'Can\'t add document in current {} monitoring status'.format(status_current))


def validate_document_conclusion_upload_allowed(request):
    status_current = request.validated['monitoring'].status
    if status_current != 'active':
        raise_operation_error(request, 'Can\'t add document in current {} monitoring status'.format(status_current))


def validate_credentials_generate(request):
    client = TendersClient(
        request.registry.api_token,
        host_url=request.registry.api_server,
        api_version=request.registry.api_version,
    )
    try:
        response = client.extract_credentials(request.validated['monitoring'].tender_id)
        if sha512(request.params.get('acc_token')).hexdigest() != response['data']['tender_token']:
            raise forbidden(request)
    except ResourceNotFound:
        raise_operation_error(request, 'Tender {} not found'.format(request.validated['monitoring'].tender_id))


def _validate_elimination_report_status(request):
    monitoring = request.validated['monitoring']
    if monitoring.status != 'addressed':
        request.errors.status = 422
        request.errors.add('body', 'eliminationResolution',
                           'Can\'t update in current {} monitoring status'.format(monitoring.status))
        raise error_handler(request.errors)


def validate_elimination_report_data(request):
    _validate_elimination_report_status(request)
    return validate_data(request, EliminationReport)


def validate_patch_elimination_report_data(request):
    _validate_elimination_report_status(request)
    return validate_data(request, EliminationReport, partial=True)
