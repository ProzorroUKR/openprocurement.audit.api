# -*- coding: utf-8 -*-
import os
import unittest
from types import FunctionType

import webtest
from paste.deploy.loadwsgi import loadapp

from openprocurement.audit.api.constants import VERSION
from openprocurement.audit.api.design import sync_design

COUCHBD_NAME_SETTING = 'couchdb.db_name'


wsgiapp = None


def loadwsgiapp(uri, **kwargs):
    global wsgiapp
    wsgiapp = wsgiapp or loadapp(uri, **kwargs)
    return wsgiapp


def snitch(func):
    """
        This method is used to add test function to TestCase classes.
        snitch method gets test function and returns a copy of this function
        with 'test_' prefix at the beginning (to identify this function as
        an executable test).
        It provides a way to implement a storage (python module that
        contains non-executable test functions) for tests and to include
        different set of functions into different test cases.
    """
    return FunctionType(func.func_code, func.func_globals,
                        'test_' + func.func_name, closure=func.func_closure)


class PrefixedTestRequest(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        prefix = '/api/{}'.format(VERSION)
        if not path.startswith(prefix):
            path = prefix + path
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseTestApp(webtest.TestApp):
    RequestClass = PrefixedTestRequest

    def __init__(self, *args, **kwargs):
        super(BaseTestApp, self).__init__(*args, **kwargs)

    def reset(self):
        super(BaseTestApp, self).reset()
        self.recreate_db()

    def recreate_db(self):
        self.drop_db()
        return self.create_db()

    def create_db(self):
        db_name = os.environ.get('DB_NAME', self.app.registry.settings[COUCHBD_NAME_SETTING])
        self.app.registry.db = self.app.registry.couchdb_server.create(db_name)
        sync_design(self.app.registry.db)
        return self.app.registry.db

    def drop_db(self):
        db_name = self.app.registry.db.name
        if db_name and db_name in self.app.registry.couchdb_server:
            self.app.registry.couchdb_server.delete(db_name)


class BaseWebTest(unittest.TestCase):
    """
    Base Web Test to test openprocurement.audit.api.
    It setups the database before each test and delete it after.
    """
    AppClass = BaseTestApp

    relative_uri = "config:tests.ini"
    relative_to = os.path.dirname(__file__)

    initial_auth = None

    @classmethod
    def setUpClass(cls):
        cls.app = cls.AppClass(loadwsgiapp(cls.relative_uri, relative_to=cls.relative_to))
        cls.couchdb_server = cls.app.app.registry.couchdb_server
        cls.db = cls.app.app.registry.db

    def setUp(self):
        self.app.authorization = self.initial_auth
        self.db = self.app.recreate_db()

    def tearDown(self):
        self.app.drop_db()
