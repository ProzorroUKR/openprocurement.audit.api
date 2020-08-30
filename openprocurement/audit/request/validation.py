# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import update_logging_context
from openprocurement.audit.api.validation import validate_data
from openprocurement.audit.request.models import Request


def validate_request_data(request):
    update_logging_context(request, {"REQUEST_ID": "__new__"})
    return validate_data(request, Request)


def validate_patch_request_data(request):
    return validate_data(request, Request, partial=True)
