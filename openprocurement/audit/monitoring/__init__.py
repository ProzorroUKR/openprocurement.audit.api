from logging import getLogger

from pyramid.events import ContextFound

from openprocurement.audit.api import AuthenticationPolicy
from openprocurement.audit.monitoring.design import add_design
from openprocurement.audit.monitoring.utils import monitoring_from_data, extract_monitoring, set_logging_context

LOGGER = getLogger(__package__)


def includeme(config):
    LOGGER.info('init audit-monitoring plugin')
    add_design()
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_monitoring, 'monitoring', reify=True)
    config.add_request_method(monitoring_from_data)
    settings = config.get_settings()
    config.registry.api_token = settings.get('api_token')
    config.registry.api_server = settings.get('api_server')
    config.registry.api_version = settings.get('api_version')
    config.scan("openprocurement.audit.monitoring.views")
