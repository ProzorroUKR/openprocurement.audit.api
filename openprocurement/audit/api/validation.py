# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context, raise_operation_error, error_handler
from openprocurement.api.validation import validate_data
from openprocurement.audit.api.models import Monitor


def validate_monitor_data(request):
    update_logging_context(request, {'MONITOR_ID': '__new__'})
    return validate_data(request, Monitor)


def validate_patch_monitor_data(request):
    return validate_data(request, Monitor, partial=True)


def validate_dialogue_data(request):
    update_logging_context(request, {'DIALOGUE_ID': '__new__'})
    model = type(request.monitor).dialogues.model_class
    return validate_data(request, model)

def validate_patch_monitor_status(request):
    status = request.validated['data'].get('status', request.context.status)
    if status == 'draft':
        pass
    elif status == 'active':
        validate_patch_monitor_active_status(request)
    else:
        raise_operation_error(request, 'Can\'t update monitor status to {}'.format(status))

def validate_patch_monitor_active_status(request):
    status_current = request.context.status
    if status_current == 'draft':
        if not request.validated['data'].get('decision'):
            request.errors.status = 403
            request.errors.add('body', 'decision', 'This field is required.')
            raise error_handler(request.errors)
    elif status_current == 'active':
        if request.json.get("data", {}).get('decision'):
            raise_operation_error(request, 'Can\'t update monitor decision in current {} status'.format(status_current))
    else:
        raise_operation_error(request, 'Can\'t update monitor status to active in current {}'.format(status_current))

def validate_document_decision_upload_allowed(request):
    status_current = request.validated['monitor'].status
    if status_current != 'draft':
        raise_operation_error(request, 'Can\'t add document in current {} monitor status'.format(status_current))

def validate_document_conclusion_upload_allowed(request):
    status_current = request.validated['monitor'].status
    if status_current != 'active':
        raise_operation_error(request, 'Can\'t add document in current {} monitor status'.format(status_current))
