# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import update_logging_context
from openprocurement.audit.api.validation import validate_data
from openprocurement.audit.inspection.models import Inspection


def validate_inspection_data(request, **_):
    update_logging_context(request, {'INSPECTION_ID': '__new__'})
    return validate_data(request, Inspection)


def validate_patch_inspection_data(request, **_):
    return validate_data(request, Inspection, partial=True)
