import os
import unittest
from types import FunctionType

import webtest
from paste.deploy.loadwsgi import loadapp

from openprocurement.audit.api.constants import VERSION
from openprocurement.audit.api.database import COLLECTION_CLASSES


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
        cls.app = cls.AppClass(loadapp(cls.relative_uri, relative_to=cls.relative_to))

        cls.mongodb = cls.app.app.registry.mongodb
        cls.clean_mongodb()

    def setUp(self):
        self.app.authorization = self.initial_auth

    def tearDown(self):
        self.clean_mongodb()

    @classmethod
    def clean_mongodb(cls):
        for collection in COLLECTION_CLASSES.keys():
            collection = getattr(cls.mongodb, collection, None)
            if collection:  # plugins are optional
                collection.flush()
        cls.mongodb.flush_sequences()
