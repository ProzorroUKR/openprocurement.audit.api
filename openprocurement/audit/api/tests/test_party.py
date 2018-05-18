# -*- coding: utf-8 -*-
import unittest
import mock
import json

from hashlib import sha512
from datetime import datetime
from freezegun import freeze_time
from openprocurement.api.constants import TZ
from openprocurement.api.utils import get_now
from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.api.tests.utils import get_errors_field_names


class MonitoringPartyResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringPartyResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                    "documents": [{
                        'title': 'lorem.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }]
                }
            }})

        self.party_creator = {
            "name": "The State Audit Service of Ukraine",
            "contactPoint": {
                "name": "Oleksii Kovalenko",
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
                "create"
            ]
        }

        self.party_dialogue = {
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
                "dialogue"
            ]
        }

    def test_party_create_required_fields(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {
                ('body', 'contactPoint'),
                ('body', 'identifier'),
                ('body', 'name'),
                ('body', 'address'),
            },
            get_errors_field_names(response, 'This field is required.'))

    def test_party_create(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': self.party_creator})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        party_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/parties/{}'.format(self.monitoring_id, party_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['name'], "The State Audit Service of Ukraine",)
        self.assertEqual(response.json['data']['roles'], ['create'])

    def test_dialogue_party_create(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': self.party_dialogue})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        party_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/parties/{}'.format(self.monitoring_id, party_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['name'], "The State Audit Service of Ukraine",)
        self.assertEqual(response.json['data']['roles'], ['dialogue'])

        response = self.app.post_json(
            '/monitorings/{}/dialogues'.format(self.monitoring_id),
            {"data": {
                "title": "Lorem ipsum",
                "description": "Lorem ipsum dolor sit amet.",
                "documents": [{
                    'title': 'ipsum.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }],
                "relatedParty": party_id
            }}, status=201)

        dialogue_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/dialogues/{}'.format(self.monitoring_id, dialogue_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['relatedParty'], party_id)

    def test_dialogue_party_create_party_id_not_exists(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': self.party_dialogue})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        party_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/parties/{}'.format(self.monitoring_id, party_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['name'], "The State Audit Service of Ukraine",)
        self.assertEqual(response.json['data']['roles'], ['dialogue'])

        response = self.app.post_json(
            '/monitorings/{}/dialogues'.format(self.monitoring_id),
            {"data": {
                "title": "Lorem ipsum",
                "description": "Lorem ipsum dolor sit amet.",
                "documents": [{
                    'title': 'ipsum.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }],
                "relatedParty": "Party with the devil"
            }}, status=422)

        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {('body', 'relatedParty')},
            get_errors_field_names(response, 'relatedParty should be one of parties.'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitoringPartyResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
