# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context, raise_operation_error, error_handler
from openprocurement.api.validation import validate_json_data, validate_data
from openprocurement.audit.api.models import Monitor


def validate_monitor_data(request):
    update_logging_context(request, {'MONITOR_ID': '__new__'})
    data = validate_json_data(request)
    if data is None:
        return
    data = validate_data(request, Monitor, data=data)
    return data


def validate_patch_monitor_data(request):
    return validate_data(request, Monitor, partial=True)

def validate_patch_monitor_status(request):
    data = request.validated['data']
    if data.get('status') == request.context.status:
        return
    elif data.get('status') == 'active':
        validate_patch_monitor_active_status(request)
    else:
        raise_operation_error(request, 'Can\'t update monitor status to {}'.format(data.get('status')))

def validate_patch_monitor_active_status(request):
    data = request.validated['data']
    if request.context.status != 'draft':
        raise_operation_error(request, 'Can\'t activate monitor in current {} status'.format(request.context.status))
    if not data['decision']:
        request.errors.status = 403
        request.errors.add('body', 'decision', 'This field is required.')
        raise error_handler(request.errors)
