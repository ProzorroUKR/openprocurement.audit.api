from logging import getLogger
from pyramid.interfaces import IRequest
from openprocurement.audit.api.adapters import ContentConfigurator
from openprocurement.audit.api.auth import AuthenticationPolicy
from openprocurement.audit.api.interfaces import IContentConfigurator, IOPContent
from openprocurement.audit.api.utils import get_content_configurator

LOGGER = getLogger(__package__)


def includeme(config):
    config.scan("openprocurement.audit.api.views")
    config.scan("openprocurement.audit.api.subscribers")
    config.set_authentication_policy(AuthenticationPolicy(config.registry.settings['auth.file']))
    config.registry.registerAdapter(ContentConfigurator, (IOPContent, IRequest), IContentConfigurator)
    config.add_request_method(get_content_configurator, 'content_configurator', reify=True)
