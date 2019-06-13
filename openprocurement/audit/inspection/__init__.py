from logging import getLogger

from pyramid.events import ContextFound

from openprocurement.audit.inspection.design import add_design
from openprocurement.audit.inspection.utils import set_logging_context, extract_inspection, inspection_from_data

LOGGER = getLogger(__package__)


def includeme(config):
    LOGGER.info('init audit-inspection plugin')
    add_design()
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_inspection, 'inspection', reify=True)
    config.add_request_method(inspection_from_data)
    config.scan("openprocurement.audit.inspection.views")
