# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context, raise_operation_error, error_handler
from openprocurement.api.validation import validate_json_data, validate_data
from openprocurement.audit.api.models import Monitor


def validate_monitor_data(request):
    update_logging_context(request, {'MONITOR_ID': '__new__'})
    data = validate_json_data(request)
    if data is not None:
        return validate_data(request, Monitor, data=data)


def validate_patch_monitor_data(request):
    return validate_data(request, Monitor, partial=True)

def validate_patch_monitor_status(request):
    status = request.validated['data'].get('status')
    status_current = request.context.status
    if status != status_current:
        if status == 'active':
            validate_patch_monitor_active_status(request)
        else:
            raise_operation_error(request, 'Can\'t update monitor status to {}'.format(status))

def validate_patch_monitor_active_status(request):
    status_current = request.context.status
    if status_current != 'draft':
        raise_operation_error(request, 'Can\'t update monitor status to active in current {}'.format(status_current))
    if not request.validated['data']['decision']:
        request.errors.status = 403
        request.errors.add('body', 'decision', 'This field is required.')
        raise error_handler(request.errors)

def validate_document_decision_upload_allowed(request):
    status_current = request.validated['monitor'].status
    if status_current != 'draft':
        raise_operation_error(request, 'Can\'t add document in current {} monitor status'.format(status_current))

def validate_document_conclusion_upload_allowed(request):
    status_current = request.validated['monitor'].status
    if status_current != 'active':
        raise_operation_error(request, 'Can\'t add document in current {} monitor status'.format(status_current))
