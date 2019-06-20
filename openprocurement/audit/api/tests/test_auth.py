# -*- coding: utf-8 -*-
import os
import unittest

from pyramid.tests.test_authentication import TestBasicAuthAuthenticationPolicy

from openprocurement.audit.api.auth import AuthenticationPolicy


class AuthTest(TestBasicAuthAuthenticationPolicy):
    def _makeOne(self, check):
        auth_file_path = "{}/auth.ini".format(os.path.dirname(os.path.abspath(__file__)))
        return AuthenticationPolicy(auth_file_path, 'SomeRealm')

    test_authenticated_userid_utf8 = None
    test_authenticated_userid_latin1 = None
