# -*- coding: utf-8 -*-
from hashlib import sha512

from openprocurement_client.client import TendersClient
from restkit import ResourceNotFound

from openprocurement.audit.api.constants import (
    CONCLUSION_OBJECT_TYPE,
    DECISION_OBJECT_TYPE,
    DRAFT_STATUS,
    ACTIVE_STATUS,
    ADDRESSED_STATUS,
    DECLINED_STATUS,
)
from openprocurement.audit.api.utils import (
    update_logging_context,
    raise_operation_error,
    error_handler,
    forbidden,
    get_now,
)
from openprocurement.audit.api.validation import validate_data
from openprocurement.audit.monitoring.models import Monitoring, EliminationReport, Party, Appeal, Post
from openprocurement.audit.monitoring.utils import get_access_token, get_monitoring_role


def validate_monitoring_data(request):
    """
    Validate monitoring data POST
    """
    update_logging_context(request, {'MONITOR_ID': '__new__'})
    data = validate_data(request, Monitoring)

    monitoring = request.validated['monitoring']
    if monitoring.status != DRAFT_STATUS:
        request.errors.add(
            'body', 'status', "Can't create a monitoring in '{}' status.".format(monitoring.status)
        )
        request.errors.status = 422
        raise error_handler(request.errors)
    return data


def validate_patch_monitoring_data(request):
    """
    Validate monitoring data PATCH
    """
    data = validate_data(request, Monitoring, partial=True)
    _validate_patch_monitoring_fields(request)
    _validate_patch_monitoring_status(request)
    return data


def validate_post_data(request):
    """
    Validate post data POST
    """
    update_logging_context(request, {'POST_ID': '__new__'})
    data = validate_data(request, Post)
    _validate_post_post_status(request)
    return data


def validate_party_data(request):
    """
    Validate party data POST
    """
    update_logging_context(request, {'PARTY_ID': '__new__'})
    return validate_data(request, Party)


def validate_patch_party_data(request):
    """
    Validate party data PATCH
    """
    data = validate_data(request, Party, partial=True)
    return data


def validate_elimination_report_data(request):
    """
    Validate elimination report data POST
    """
    if request.validated["monitoring"].eliminationReport is not None:
        raise_operation_error(request, "Can't post another elimination report.")
    _validate_elimination_report_status(request)
    return validate_data(request, EliminationReport)


def validate_appeal_data(request):
    """
    Validate appeal report data POST
    """
    monitoring = request.validated['monitoring']
    if monitoring.appeal is not None:
        raise_operation_error(request, "Can't post another appeal.")

    if monitoring.conclusion is None or monitoring.conclusion.datePublished is None:
        request.errors.status = 422
        request.errors.add('body', 'appeal', 'Can\'t post before conclusion is published.')
        raise error_handler(request.errors)

    return validate_data(request, Appeal)

def validate_document_decision_status(request):
    _validate_document_status(request, DRAFT_STATUS)


def validate_document_conclusion_status(request):
    _validate_document_status(request, ACTIVE_STATUS)


def validate_document_post_status(request):
    post = request.validated['post']

    if post.author != get_monitoring_role(request.authenticated_role):
        raise forbidden(request)

    if post.postOf == DECISION_OBJECT_TYPE:
        _validate_document_status(request, ACTIVE_STATUS)
    elif post.postOf == CONCLUSION_OBJECT_TYPE:
        _validate_document_status(request, (ADDRESSED_STATUS, DECLINED_STATUS))


def validate_credentials_generate(request):
    try:
        token = get_access_token(request)
    except ValueError:
        raise_operation_error(request, 'No access token was provided.')

    try:
        response = TendersClient(
            request.registry.api_token,
            host_url=request.registry.api_server,
            api_version=request.registry.api_version,
        ).extract_credentials(request.validated['monitoring'].tender_id)
    except ResourceNotFound:
        raise_operation_error(request, 'Tender {} not found'.format(request.validated['monitoring'].tender_id))
    else:
        if sha512(token).hexdigest() != response['data']['tender_token']:
            raise forbidden(request)


def _validate_patch_monitoring_fields(request):
    """
    Check sent data that is not allowed in current status
    acceptable fields are set in Monitor.Options.roles: edit_draft, edit_active, etc
    """
    provided = set(request.validated['json_data'].keys())
    allowed = set(request.validated['data'].keys())
    difference = provided - allowed
    if difference:
        for i in difference:
            request.errors.add('body', i, 'This field cannot be updated in the {} status.'.format(
                request.validated['monitoring']['status']))
        request.errors.status = 422
        raise error_handler(request.errors)


def _validate_patch_monitoring_status(request):
    """
    Check that monitoring status change is allowed
    """
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
        raise_operation_error(request, 'Can\'t set {} status to monitoring if no violation occurred.'.format(
            ADDRESSED_STATUS))


def _validate_patch_monitoring_status_active_to_declined(request):
    _validate_patch_monitoring_status_active_to_addressed_or_declined(request)
    if request.validated.get('data', {}).get('conclusion').get('violationOccurred'):
        raise_operation_error(request, 'Can\'t set {} status to monitoring if violation occurred.'.format(
            DECLINED_STATUS))


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
        request.errors.add('body', 'cancellation', 'This field is required.')
        raise error_handler(request.errors)


def _validate_post_post_status(request):
    post = request.validated['post']
    monitoring = request.validated['monitoring']
    status_current = monitoring.status
    if status_current in (ADDRESSED_STATUS, DECLINED_STATUS):
        if request.authenticated_userid == monitoring.tender_owner:
            if any(post.postOf == CONCLUSION_OBJECT_TYPE and post.relatedPost is None for post in monitoring.posts):
                raise_operation_error(request, 'Can\'t add more than one {} post in current {} monitoring status.'.format(
                    CONCLUSION_OBJECT_TYPE, status_current))
        elif post.relatedPost is None:
            raise_operation_error(request, 'Can\'t add post in current {} monitoring status.'.format(
                status_current))
    elif status_current not in (ACTIVE_STATUS,):
        raise_operation_error(request, 'Can\'t add post in current {} monitoring status.'.format(
            status_current))


def _validate_elimination_report_status(request):
    monitoring = request.validated['monitoring']
    if monitoring.status != ADDRESSED_STATUS:
        request.errors.status = 422
        request.errors.add('body', 'eliminationReport',
                           'Can\'t update in current {} monitoring status.'.format(monitoring.status))
        raise error_handler(request.errors)


def _validate_document_status(request, status):
    status_current = request.validated['monitoring'].status
    statuses = status if isinstance(status, tuple) else (status,)
    if status_current not in statuses:
        raise_operation_error(request, 'Can\'t add document in current {} monitoring status.'.format(status_current))
