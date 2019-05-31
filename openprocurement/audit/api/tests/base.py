# -*- coding: utf-8 -*-

import unittest
import webtest
import os
from copy import deepcopy
from openprocurement.api.constants import VERSION, SANDBOX_MODE
from uuid import uuid4
from urllib import urlencode
from base64 import b64encode
from datetime import datetime
import ConfigParser


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        prefix = '/api/{}'.format(VERSION)
        if not path.startswith(prefix):
            path = prefix + path
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(unittest.TestCase):
    """
    Base Web Test to test openprocurement.planning.api.

    It setups the database before each test and delete it after.
    """
    initial_data = {
        "tender_id": "f" * 32,
        "reasons": ["indicator"],
        "procuringStages": ["planning"]
    }

    initial_party = {
        "name": "The State Audit Service of Ukraine",
        "contactPoint": {
            "name": "Jane Doe",
            "telephone": "0440000000"
        },
        "identifier": {
            "scheme": "UA-EDR",
            "id": "40165856",
            "uri": "http://www.dkrs.gov.ua"
        },
        "address": {
            "countryName": "Ukraine",
            "postalCode": "04070",
            "region": "Kyiv",
            "streetAddress": "Petra Sahaidachnoho St, 4",
            "locality": "Kyiv"
        },
        "roles": [
            "sas"
        ]
    }

    acceleration = {
        'monitoringDetails': 'accelerator=1440'
    }

    def setUp(self):
        self.app = webtest.TestApp("config:tests.ini", relative_to=os.path.dirname(__file__))
        self.app.RequestClass = PrefixedRequestClass
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db
        self.app.app.registry.docservice_url = 'http://localhost'

        self.broker_name = "broker"
        self.broker_pass = "broker"
        self.sas_name = "test_sas"
        self.sas_pass = "test_sas_token"
        self.risk_indicator_name = "risk_indicator_bot"
        self.risk_indicator_pass = "test_risk_indicator_bot_token"

    def tearDown(self):
        del self.couchdb_server[self.db.name]

    def create_monitoring(self, **kwargs):

        data = deepcopy(self.initial_data)

        if SANDBOX_MODE:
            data.update(self.acceleration)

        data.update(kwargs)

        authorization = getattr(self.app, "authorization", None)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/monitorings', {'data': data})
        monitoring = response.json['data']
        self.monitoring_id = monitoring['id']

        self.app.authorization = authorization

        return monitoring

    def create_active_monitoring(self, **kwargs):
        self.create_monitoring(**kwargs)
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": datetime.now().isoformat()
                },
                "status": "active",
            }}
        )
        self.app.authorization = None
        return response.json['data']

class DSWebTestMixin(object):
    def generate_docservice_url(self):
        uuid = uuid4().hex
        key = self.app.app.registry.docservice_key
        keyid = key.hex_vk()[:8]
        signature = b64encode(key.signature("{}\0{}".format(uuid, '0' * 32)))
        query = {'Signature': signature, 'KeyID': keyid}
        return '{}/get/{}?{}'.format(self.app.app.registry.docservice_url, uuid, urlencode(query))
