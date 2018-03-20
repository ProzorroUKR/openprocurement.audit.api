# -*- coding: utf-8 -*-
import unittest
import webtest
import os
from copy import deepcopy
from openprocurement.api.constants import VERSION, SESSION
import ConfigParser


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '/api/%s%s' % (VERSION, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test openprocurement.planning.api.

    It setups the database before each test and delete it after.
    """

    def setUp(self):
        self.app = webtest.TestApp("config:tests.ini", relative_to=os.path.dirname(__file__))
        self.app.RequestClass = PrefixedRequestClass
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db

        config = ConfigParser.RawConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'auth.ini'))
        self.broker_token = config.get("brokers", "broker")
        self.sas_token = config.get("sas", "test_sas")

    def tearDown(self):
        del self.couchdb_server[self.db.name]


class BaseMonitorWebTest(BaseWebTest):
    initial_data = {
        "tender_id": "f" * 32,
        "status": "draft",
    }

    def setUp(self):
        super(BaseMonitorWebTest, self).setUp()
        self.create_monitor()

    def create_monitor(self):
        data = deepcopy(self.initial_data)
        self.app.authorization = ('Basic', (self.sas_token, ''))

        response = self.app.post_json('/monitors', {'data': data})
        monitor = response.json['data']
        self.monitor_token = response.json['access']['token']
        self.monitor_id = monitor['id']

        self.app.authorization = None

    def tearDown(self):
        del self.db[self.monitor_id]
        super(BaseMonitorWebTest, self).tearDown()
