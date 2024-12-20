# -*- coding: utf-8 -*-
import base64
import os
import unittest
from hashlib import sha512

from pyramid import testing
from pyramid.compat import bytes_

from openprocurement.audit.api.auth import AuthenticationPolicy


class AuthTest(unittest.TestCase):
    def _makeOne(self, *args, **kwargs):
        auth_file_path = "{}/auth.ini".format(os.path.dirname(os.path.abspath(__file__)))
        return AuthenticationPolicy(auth_file_path, 'SomeRealm')

    def test_unauthenticated_userid(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Basic %s' % base64.b64encode(bytes_('chrisr:password')).decode('ascii')
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), 'chrisr')

    def test_unauthenticated_userid_no_credentials(self):
        request = testing.DummyRequest()
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), None)

    def test_unauthenticated_bad_header(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = '...'
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), None)

    def test_unauthenticated_userid_not_basic(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Complicated things'
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), None)

    def test_unauthenticated_userid_corrupt_base64(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Basic chrisr:password'
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), None)

    def test_authenticated_userid(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Basic %s' % base64.b64encode(bytes_('chrisr:password')).decode('ascii')

        def check(username, password, request):
            return []

        policy = self._makeOne(check)
        self.assertEqual(policy.authenticated_userid(request), 'chrisr')

    def test_unauthenticated_userid_invalid_payload(self):
        request = testing.DummyRequest()
        request.headers['Authorization'] = 'Basic %s' % base64.b64encode(bytes_('chrisrpassword')).decode('ascii')
        policy = self._makeOne(None)
        self.assertEqual(policy.unauthenticated_userid(request), None)

    def test_remember(self):
        policy = self._makeOne(None)
        self.assertEqual(policy.remember(None, None), [])

    def test_forget(self):
        policy = self._makeOne(None)
        self.assertEqual(policy.forget(None), [('WWW-Authenticate', 'Basic realm="SomeRealm"')])

    def test_principals_acc_token_param(self):
        request = testing.DummyRequest()
        request.params["acc_token"] = "token"
        self.assertPrincipals(request, "token")

    def test_principals_acc_token_param_utf8(self):
        request = testing.DummyRequest()
        request.params["acc_token"] = b'm\xc3\xb6rk\xc3\xb6'.decode("utf8")
        self.assertPrincipals(request, b'm\xc3\xb6rk\xc3\xb6'.decode("utf8"))

    def test_principals_acc_token_header(self):
        request = testing.DummyRequest()
        request.headers["X-Access-Token"] = "token"
        self.assertPrincipals(request, "token")

    def test_principals_acc_token_header_utf8(self):
        request = testing.DummyRequest()
        request.headers["X-Access-Token"] = b'm\xc3\xb6rk\xc3\xb6'.decode("utf8")
        self.assertPrincipals(request, b'm\xc3\xb6rk\xc3\xb6'.decode("utf8"))

    def test_principals_acc_token_body(self):
        request = testing.DummyRequest()
        request.content_type = "application/json"
        request.method = "POST"
        request.json_body = {'access': {"token": "token"}}
        self.assertPrincipals(request, "token")

    def test_principals_acc_token_body_utf8(self):
        request = testing.DummyRequest()
        request.content_type = "application/json"
        request.method = "POST"
        request.json_body = {'access': {"token": b'm\xc3\xb6rk\xc3\xb6'.decode("utf8")}}
        self.assertPrincipals(request, b'm\xc3\xb6rk\xc3\xb6'.decode("utf8"))

    def assertPrincipals(self, request, acc_token):
        policy = self._makeOne(None)
        principals = policy.check("chrisr", "password", request)
        self.assertIn("g:tests", principals)
        self.assertIn("chrisr_{}".format(acc_token), principals)
        self.assertIn("chrisr_{}".format(sha512(acc_token.encode("utf-8")).hexdigest()), principals)
