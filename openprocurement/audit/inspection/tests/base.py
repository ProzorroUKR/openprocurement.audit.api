# -*- coding: utf-8 -*-
import os
from base64 import b64encode
from urllib.parse import urlencode
from nacl.encoding import HexEncoder
from openprocurement.audit.api.tests.base import BaseWebTest as BaseApiWebTest
from uuid import uuid4
from unittest import mock


class BaseWebTest(BaseApiWebTest):
    relative_to = os.path.dirname(__file__)

    def setUp(self):
        super(BaseWebTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.broker_name = "broker"
        self.broker_pass = "broker"
        self.broker_name_r = "brokerr"
        self.broker_pass_r = "brokerr"
        self.sas_name = "test_sas"
        self.sas_pass = "test_sas_token"

    def generate_docservice_url(self, doc_hash=None):
        uuid = uuid4().hex
        doc_hash = doc_hash or '0' * 32
        registry = self.app.app.registry
        signer = registry.docservice_key
        keyid = signer.verify_key.encode(encoder=HexEncoder)[:8].decode()
        msg = "{}\0{}".format(uuid, doc_hash).encode()
        signature = b64encode(signer.sign(msg).signature)
        query = {'Signature': signature, 'KeyID': keyid}
        return '{}/get/{}?{}'.format(registry.docservice_url, uuid, urlencode(query))

    def create_inspection(self, restricted_config=False, **kwargs):
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
        with mock.patch(
        'openprocurement.audit.inspection.views.inspection.extract_restricted_config_from_monitoring'
        ) as mock_get_monitoring:
            mock_get_monitoring.return_value = restricted_config
            response = self.app.post_json('/inspections', {'data': data})

        self.inspection_id = response.json['data']['id']
        self.inspectionId = response.json['data']['inspection_id']
        self.document_id = response.json['data']['documents'][0]["id"]
        self.monitoring_ids = response.json['data']['monitoring_ids']
        self.app.authorization = None

        return response.json['data']
