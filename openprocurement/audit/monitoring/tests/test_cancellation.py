# -*- coding: utf-8 -*-
import unittest

from openprocurement.audit.api.constants import CANCELLED_STATUS
from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


class MonitoringCancellationResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringCancellationResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring(parties=[self.initial_party])
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

    def test_cancellation_get(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description'
                }
            }})
        response = self.app.get('/monitorings/{}/cancellation'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEquals('some_description', response.json['data']['description'])

    def test_get_cancellation_from_active_monitoring(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        with self.assertRaisesRegexp(Exception, 'Bad response: 403 Forbidden'):
            response = self.app.get('/monitorings/{}/cancellation'.format(self.monitoring_id))
            self.assertEqual(response.status_code, 404)

    def test_decision_party_create(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        party_id = response.json['data']['parties'][0]['id']

        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                'cancellation': {
                    'description': 'some_description',
                    "relatedParty": party_id
                }
            }}
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['cancellation']['relatedParty'], party_id)

    def test_dialogue_party_create_party_id_not_exists(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "cancellation": {
                    "description": "some_description",
                    "relatedParty": "Party with the devil"
                }
            }}, status=422
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'cancellation', 'relatedParty'),
            next(get_errors_field_names(response, 'relatedParty should be one of parties.')))

    def test_restricted_visibility(self):
        self.create_monitoring(parties=[self.initial_party], restricted_config=True)
        self.app.patch_json(
            f'/monitorings/{self.monitoring_id}',
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description',
                    'documents': [
                        {
                            'title': 'lorem.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    ]
                }
            }}
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["cancellation"]["description"], "some_description")
        self.assertEqual(response.json['data']["cancellation"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["cancellation"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["cancellation"]["description"], "some_description")
        self.assertEqual(response.json['data']["cancellation"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["cancellation"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["cancellation"]["description"], "Приховано")
        self.assertEqual(response.json['data']["cancellation"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["cancellation"]["documents"][0]["url"], "Приховано")
