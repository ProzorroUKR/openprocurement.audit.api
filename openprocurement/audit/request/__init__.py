from logging import getLogger

from pyramid.events import ContextFound

from openprocurement.audit.api import AuthenticationPolicy
from openprocurement.audit.request.design import add_design
from openprocurement.audit.request.utils import (
    set_logging_context,
    extract_request,
    request_from_data,
)

LOGGER = getLogger(__package__)


def includeme(config):
    LOGGER.info("init audit-request plugin")
    config.set_authentication_policy(
        AuthenticationPolicy(config.registry.settings["auth.file"])
    )
    add_design()
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_request, "request", reify=True)
    config.add_request_method(request_from_data)
    config.scan("openprocurement.audit.request.views")
