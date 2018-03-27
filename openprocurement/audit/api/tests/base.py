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
        prefix = '/api/{}'.format(VERSION)
        if not path.startswith(prefix):
            path = prefix + path
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test openprocurement.planning.api.

    It setups the database before each test and delete it after.
    """
    initial_data = {
        "tender_id": "f" * 32,
        "status": "draft",
    }

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

    def create_monitor(self, **kwargs):

        data = deepcopy(self.initial_data)
        data.update(kwargs)
        self.app.authorization = ('Basic', (self.sas_token, ''))

        response = self.app.post_json('/monitors', {'data': data})
        monitor = response.json['data']
        self.monitor_token = response.json['access']['token']
        self.monitor_id = monitor['id']

        self.app.authorization = None

        return monitor
