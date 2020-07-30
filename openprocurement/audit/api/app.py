# -*- coding: utf-8 -*-

def is_test():
    return any([
        'test' in __import__('sys').argv[0],
        'PYTEST_XDIST_WORKER' in __import__('os').environ])

if not is_test():
    import gevent.monkey
    gevent.monkey.patch_all()

import os
import simplejson
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from pkg_resources import iter_entry_points
from pyramid.authorization import ACLAuthorizationPolicy as AuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON, JSONP
from pyramid.settings import asbool

from openprocurement.audit.api.auth import AuthenticationPolicy, authenticated_role, check_accreditation
from openprocurement.audit.api.constants import ROUTE_PREFIX
from openprocurement.audit.api.database import init_db
from openprocurement.audit.api.utils import forbidden, request_params


def main(global_config, **settings):
    config = Configurator(
        autocommit=True,
        settings=settings,
        authentication_policy=AuthenticationPolicy(settings['auth.file'], __name__),
        authorization_policy=AuthorizationPolicy(),
        route_prefix=ROUTE_PREFIX,
    )
    config.include('pyramid_exclog')
    config.include("cornice")
    config.add_forbidden_view(forbidden)
    config.add_request_method(request_params, 'params', reify=True)
    config.add_request_method(authenticated_role, reify=True)
    config.add_request_method(check_accreditation)
    config.add_renderer('json', JSON(serializer=simplejson.dumps))
    config.add_renderer('prettyjson', JSON(indent=4, serializer=simplejson.dumps))
    config.add_renderer('jsonp', JSONP(param_name='opt_jsonp', serializer=simplejson.dumps))
    config.add_renderer('prettyjsonp', JSONP(indent=4, param_name='opt_jsonp', serializer=simplejson.dumps))

    # db connection
    db_name = os.environ.get('MONGODB_DATABASE', settings['db_name'])
    db_uri = os.environ.get('MONGODB_URI', settings['mongodb_uri'])
    init_db(db_uri, db_name)

    # search for plugins
    plugins = settings.get('plugins') and settings['plugins'].split(',')
    for entry_point in iter_entry_points('openprocurement.audit.api.plugins'):
        if not plugins or entry_point.name in plugins:
            plugin = entry_point.load()
            plugin(config)
            pass

    # Document Service key
    config.registry.docservice_url = settings.get('docservice_url')
    config.registry.docservice_username = settings.get('docservice_username')
    config.registry.docservice_password = settings.get('docservice_password')
    config.registry.docservice_upload_url = settings.get('docservice_upload_url')

    signing_key = settings.get('dockey', '')
    signer = SigningKey(signing_key, encoder=HexEncoder) if signing_key else SigningKey.generate()
    config.registry.docservice_key = signer
    verifier = signer.verify_key

    config.registry.keyring = {
        verifier.encode(encoder=HexEncoder)[:8].decode(): verifier
    }
    dockeys = settings.get('dockeys', '')
    for key in dockeys.split('\0'):
        if key:
            config.registry.keyring[key[:8]] = VerifyKey(key, encoder=HexEncoder)

    config.registry.server_id = settings.get('id', '')

    # search subscribers
    subscribers_keys = [k for k in settings if k.startswith('subscribers.')]
    for k in subscribers_keys:
        subscribers = settings[k].split(',')
        for subscriber in subscribers:
            for entry_point in iter_entry_points('openprocurement.{}'.format(k), subscriber):
                if entry_point:
                    plugin = entry_point.load()
                    plugin(config)

    config.registry.health_threshold = float(settings.get('health_threshold', 512))
    config.registry.health_threshold_func = settings.get('health_threshold_func', 'all')
    config.registry.update_after = asbool(settings.get('update_after', True))
    config.registry.disable_opt_fields_filter = asbool(settings.get('disable_opt_fields_filter', False))
    return config.make_wsgi_app()
