# -*- coding: utf-8 -*-

import ConfigParser
import os
from base64 import b64encode
from urllib import urlencode

from openprocurement.audit.api.tests.base import BaseWebTest as BaseApiWebTest
from uuid import uuid4


class BaseWebTest(BaseApiWebTest):
    relative_to = os.path.dirname(__file__)

    def setUp(self):
        super(BaseWebTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.broker_name = "broker"
        self.broker_pass = "broker"
        self.sas_name = "test_sas"
        self.sas_pass = "test_sas_token"

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
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/inspections', {'data': data})

        self.inspection_id = response.json['data']['id']
        self.inspectionId = response.json['data']['inspection_id']
        self.document_id = response.json['data']['documents'][0]["id"]
        self.monitoring_ids = response.json['data']['monitoring_ids']
        self.app.authorization = None

        return response.json['data']
