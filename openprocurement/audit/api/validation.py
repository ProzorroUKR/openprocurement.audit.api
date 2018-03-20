# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context
from openprocurement.api.validation import validate_json_data, validate_data
from openprocurement.audit.api.models import Monitor


def validate_monitor_data(request):
    update_logging_context(request, {'monitor_id': '__new__'})
    data = validate_json_data(request)
    if data is None:
        return
    data = validate_data(request, Monitor, data=data)
    return data


def validate_patch_monitor_data(request):
    return validate_data(request, Monitor, partial=True)
