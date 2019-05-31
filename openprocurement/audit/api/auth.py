# -*- coding: utf-8 -*-
from pyramid.authentication import BasicAuthAuthenticationPolicy, b64decode
from ConfigParser import ConfigParser
from hashlib import sha512


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

            if user['password'] == sha512(password).hexdigest():
                auth_groups = ['g:{}'.format(user['group'])]

                token = request.params.get('acc_token')
                if not token:
                    token = request.headers.get('X-Access-Token')
                    if not token:
                        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
                            try:
                                json = request.json_body
                            except ValueError:
                                json = None
                            token = isinstance(json, dict) and json.get('access', {}).get('token')
                if token:
                    auth_groups.append('{}_{}'.format(username, token))
                    auth_groups.append('{}_{}'.format(username, sha512(token).hexdigest()))

                return auth_groups
