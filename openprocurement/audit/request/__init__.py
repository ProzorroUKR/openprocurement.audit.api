from logging import getLogger

from pyramid.events import ContextFound

from openprocurement.audit.api.database import COLLECTION_CLASSES
from openprocurement.audit.request.database import RequestCollection
from openprocurement.audit.request.utils import (
    extract_request,
    request_from_data,
    set_logging_context,
)

LOGGER = getLogger(__package__)


def includeme(config):
    LOGGER.info("init audit-request plugin")
    COLLECTION_CLASSES["request"] = RequestCollection
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_request, "request", reify=True)
    config.add_request_method(request_from_data)
    config.scan("openprocurement.audit.request.views")
