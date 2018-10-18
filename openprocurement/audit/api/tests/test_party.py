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
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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

    def test_party_create_required_fields(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': {}}, status=422)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {
                ('body', 'contactPoint'),
                ('body', 'identifier'),
                ('body', 'name'),
                ('body', 'address'),
            },
            set(get_errors_field_names(response, 'This field is required.')))

    def test_party_create(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': self.initial_party})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        party_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/parties/{}'.format(self.monitoring_id, party_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['name'], "The State Audit Service of Ukraine",)
        self.assertEqual(response.json['data']['roles'], ['sas'])

    def test_party_patch(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': self.initial_party})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        party_id = response.json['data']['id']
        response = self.app.patch_json(
            '/monitorings/{}/parties/{}'.format(self.monitoring_id, party_id),
            {'data': {
                # trying to update party id. Right now it will be silently ommited
                "id": "43c4c5ec776549c6becdd874887edead",
                "name": "The NEW State Audit Service of Ukraine",
                "contactPoint": {
                    "telephone": "0449999999"
                },
                "address": {
                    "region": "Kharkov",
                    "locality": "Kharkov"
                },
            }})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual('0449999999', response.json['data']['contactPoint']['telephone'])
        self.assertEqual('Kharkov', response.json['data']['address']['region'])
        self.assertEqual('Kharkov', response.json['data']['address']['locality'])
        # ensure that id is not updated
        self.assertEqual(party_id, response.json['data']['id'])

    def test_party_get_empty_list(self):
        response = self.app.get('/monitorings/{}/parties'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 0)

    def test_party_get_list(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.post_json(
            '/monitorings/{}/parties'.format(self.monitoring_id),
            {'data': self.initial_party})

        response = self.app.get('/monitorings/{}/parties'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['name'], "The State Audit Service of Ukraine")

    def test_party_get_missing(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        with self.assertRaisesRegexp(Exception, 'Bad response: 404 Not Found'):
            response = self.app.get('/monitorings/{}/parties/{}'.format(self.monitoring_id, 'not_existent_id'))
            self.assertEqual(response.status_code, 404)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitoringPartyResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
