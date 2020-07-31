# -*- coding: utf-8 -*-
from configparser import ConfigParser
from hashlib import sha512

from pyramid.authentication import BasicAuthAuthenticationPolicy


class AuthenticationPolicy(BasicAuthAuthenticationPolicy):
    def __init__(self, auth_file, realm='Realm', debug=False):
        self.realm = realm
        self.debug = debug

        config = ConfigParser()
        config.read(auth_file)
        self.users = {}
        for group in config.sections():
            for name, password in config.items(group):
                self.users[name] = {
                    'password': password,
                    'group': group
                }

    def check(self, username, password, request):
        if username in self.users:
            user = self.users[username]
            if user['password'] == sha512(password.encode('utf8')).hexdigest():
                auth_groups = self._get_user_auth_groups(user)
                token = self._get_access_token(request)
                if token:
                    auth_groups.append('{}_{}'.format(username, token))
                    auth_groups.append('{}_{}'.format(username, sha512(token.encode('utf8')).hexdigest()))
                return auth_groups

    def _get_user_auth_groups(self, user):
        auth_groups = ["g:{}".format(user["group"])]
        return auth_groups

    def _get_access_token(self, request):
        token = request.params.get("acc_token") or request.headers.get("X-Access-Token")
        if not token and request.method in ["POST", "PUT", "PATCH"] and request.content_type == "application/json":
            try:
                json = request.json_body
            except ValueError:
                json = None
            token = json.get("access", {}).get("token") if isinstance(json, dict) else None
        return token

def get_local_roles(context):
    from pyramid.location import lineage
    roles = {}
    for location in lineage(context):
        try:
            local_roles = location.__local_roles__
        except AttributeError:
            continue
        if local_roles and callable(local_roles):
            local_roles = local_roles()
        roles.update(local_roles)
    return roles


def authenticated_role(request):
    principals = request.effective_principals
    if hasattr(request, 'context'):
        roles = get_local_roles(request.context)
        local_roles = [roles[i] for i in reversed(principals) if i in roles]
        if local_roles:
            return local_roles[0]
    groups = [g for g in reversed(principals) if g.startswith('g:')]
    return groups[0][2:] if groups else 'anonymous'


def check_accreditation(request, level):
    return "a:{}".format(level) in request.effective_principals
