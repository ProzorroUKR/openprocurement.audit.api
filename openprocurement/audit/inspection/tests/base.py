# -*- coding: utf-8 -*-

import ConfigParser
import os
import unittest
from base64 import b64encode
from urllib import urlencode

import webtest
from openprocurement.api.constants import VERSION
from uuid import uuid4


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        prefix = '/api/{}'.format(VERSION)
        if not path.startswith(prefix):
            path = prefix + path
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):

    def setUp(self):
        self.app = webtest.TestApp("config:tests.ini", relative_to=os.path.dirname(__file__))
        self.app.RequestClass = PrefixedRequestClass
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db
        self.app.app.registry.docservice_url = 'http://localhost'

        config = ConfigParser.RawConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'auth.ini'))
        self.broker_token = config.get("brokers", "broker")
        self.sas_token = config.get("sas", "test_sas")

    def tearDown(self):
        del self.couchdb_server[self.db.name]

    def generate_docservice_url(self):
        uuid = uuid4().hex
        key = self.app.app.registry.docservice_key
        keyid = key.hex_vk()[:8]
        signature = b64encode(key.signature("{}\0{}".format(uuid, '0' * 32)))
        query = {'Signature': signature, 'KeyID': keyid}
        return '{}/get/{}?{}'.format(self.app.app.registry.docservice_url, uuid, urlencode(query))

    def create_inspection(self, **kwargs):
        data = {
            "monitoring_ids": ["f" * 32, "e" * 32, "d" * 32],
            "description": "Yo-ho-ho",
            "documents": [
                {
                    'title': 'lorem.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }
            ]
        }
        data.update(kwargs)
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/inspections', {'data': data})

        self.inspection_id = response.json['data']['id']
        self.inspectionId = response.json['data']['inspection_id']
        self.document_id = response.json['data']['documents'][0]["id"]
        self.monitoring_ids = response.json['data']['monitoring_ids']
        self.app.authorization = None

        return response.json['data']
