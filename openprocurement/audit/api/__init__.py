from pyramid.events import ContextFound
from openprocurement.audit.api.design import add_design
from openprocurement.audit.api.utils import monitor_from_data, extract_monitor, set_logging_context
from logging import getLogger
from pkg_resources import get_distribution

PKG = get_distribution(__package__)

LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('init audit plugin')
    add_design()
    config.add_subscriber(set_logging_context, ContextFound)
    config.add_request_method(extract_monitor, 'monitor', reify=True)
    config.add_request_method(monitor_from_data)
    config.scan("openprocurement.audit.api.views")
