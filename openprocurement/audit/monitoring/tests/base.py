# -*- coding: utf-8 -*-
import os
from base64 import b64encode
from copy import deepcopy
from urllib.parse import urlencode
from nacl.encoding import HexEncoder
from openprocurement.audit.api.tests.base import BaseWebTest as BaseApiWebTest
from datetime import datetime
from uuid import uuid4
from unittest import mock

from openprocurement.audit.api.constants import SANDBOX_MODE


class BaseWebTest(BaseApiWebTest):
    """
    Base Web Test to test openprocurement.monitoring.api.

    It setups the database before each test and delete it after.
    """
    relative_to = os.path.dirname(__file__)

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
        super(BaseWebTest, self).setUp()
        self.broker_name = "broker"
        self.broker_pass = "broker"
        self.sas_name = "test_sas"
        self.sas_pass = "test_sas_token"
        self.risk_indicator_name = "risk_indicator_bot"
        self.risk_indicator_pass = "test_risk_indicator_bot_token"
        self.admin_name = "test"
        self.admin_pass = "token"

    def create_monitoring(self, restricted_config=False, **kwargs):

        data = deepcopy(self.initial_data)

        if SANDBOX_MODE:
            data.update(self.acceleration)

        data.update(kwargs)

        authorization = getattr(self.app, "authorization", None)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        with mock.patch('openprocurement.audit.monitoring.utils.TendersClient') as mock_api_client:
            mock_api_client.return_value.get_tender.return_value = {'config': {'restricted': restricted_config}}
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
