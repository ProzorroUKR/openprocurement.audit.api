from logging import getLogger

from pyramid.events import ContextFound

from openprocurement.audit.api.database import COLLECTION_CLASSES
from openprocurement.audit.inspection.database import InspectionCollection
from openprocurement.audit.inspection.utils import extract_inspection, inspection_from_data, set_logging_context

LOGGER = getLogger(__package__)


def includeme(config):
    LOGGER.info("init audit-inspection plugin")
    COLLECTION_CLASSES["inspection"] = InspectionCollection
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_inspection, "inspection", reify=True)
    config.add_request_method(inspection_from_data)
    config.scan("openprocurement.audit.inspection.views")
