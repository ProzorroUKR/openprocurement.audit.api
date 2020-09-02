# -*- coding: utf-8 -*-
import os
from base64 import b64encode
from urllib.parse import urlencode
from nacl.encoding import HexEncoder

from openprocurement.audit.api.choices import VIOLATION_TYPE_CHOICES
from openprocurement.audit.api.tests.base import BaseWebTest as BaseApiWebTest
from uuid import uuid4


class BaseWebTest(BaseApiWebTest):
    relative_to = os.path.dirname(__file__)

    def setUp(self):
        super(BaseWebTest, self).setUp()
        self.app.app.registry.docservice_url = "http://localhost"
        self.broker_name = "broker"
        self.broker_pass = "broker"
        self.sas_name = "test_sas"
        self.sas_pass = "test_sas_token"
        self.public_name = "public"
        self.public_pass = "public"

    def generate_docservice_url(self, doc_hash=None):
        uuid = uuid4().hex
        doc_hash = doc_hash or "0" * 32
        registry = self.app.app.registry
        signer = registry.docservice_key
        keyid = signer.verify_key.encode(encoder=HexEncoder)[:8].decode()
        msg = "{}\0{}".format(uuid, doc_hash).encode()
        signature = b64encode(signer.sign(msg).signature)
        query = {"Signature": signature, "KeyID": keyid}
        return "{}/get/{}?{}".format(registry.docservice_url, uuid, urlencode(query))

    def create_request(self, **kwargs):
        data = {
            "tenderId": "f" * 32,
            "description": "Yo-ho-ho",
            "violationType": VIOLATION_TYPE_CHOICES,
            "parties": [
                {
                    "name": "party name",
                    "address": {
                        "streetAddress": "test street address",
                        "locality": "test locality",
                        "region": "test region",
                        "postalCode": "test postalCode",
                        "countryName": "test country",
                    },
                    "contactPoint": {
                        "email": "test@example.com"
                    }
                }
            ],
            "documents": [
                {
                    "title": "lorem.doc",
                    "url": self.generate_docservice_url(),
                    "hash": "md5:" + "0" * 32,
                    "format": "application/msword",
                }
            ]
        }
        data.update(kwargs)
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        response = self.app.post_json("/requests", {"data": data})

        self.request_id = response.json["data"]["id"]
        self.requestId = response.json["data"]["requestId"]
        self.document_id = response.json["data"]["documents"][0]["id"]
        self.app.authorization = None

        return response.json["data"]
