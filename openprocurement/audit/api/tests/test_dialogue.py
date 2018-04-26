# -*- coding: utf-8 -*-
import unittest
import mock

from hashlib import sha512
from datetime import datetime
from freezegun import freeze_time
from openprocurement.api.constants import TZ
from openprocurement.api.utils import get_now
from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.api.tests.utils import get_errors_field_names


@freeze_time('2018-01-01T12:00:00.000000+03:00')
class MonitorDialogueResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitorDialogueResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitor()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.test_monitor_activation_data = {
            "status": "active",
            "decision": {
                "date": "2015-05-10T23:11:39.720908+03:00",
                "description": "text",
                "documents": [self.test_docservice_document_data]
            }
        }
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {'data': self.test_monitor_activation_data})

    def test_dialogue_create_required_fields(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {'data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {('body', 'title'), ('body', 'description')},
            get_errors_field_names(response, 'This field is required.'))

    def test_dialogue_create_by_monitor_owner(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        dialogue_id = response.json['data']['id']

        response = self.app.get('/monitors/{}/dialogues/{}'.format(self.monitor_id, dialogue_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Lorem ipsum')
        self.assertEqual(response.json['data']['description'], 'Lorem ipsum dolor sit amet')
        self.assertEqual(response.json['data']['dateSubmitted'], get_now().isoformat())

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_dialogue_create_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/credentials?acc_token={}'.format(self.monitor_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        dialogue_id = response.json['data']['id']

        response = self.app.get('/monitors/{}/dialogues/{}'.format(self.monitor_id, dialogue_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Lorem ipsum')
        self.assertEqual(response.json['data']['description'], 'Lorem ipsum dolor sit amet')
        self.assertEqual(response.json['data']['dateSubmitted'], get_now().isoformat())

    def test_monitor_owner_patch_dialogue_by_monitor_owner(self):
        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        dialogue_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/dialogues/{}?acc_token={}'.format(self.monitor_id, dialogue_id, self.monitor_token),
            {'data': {
                'title': 'It’s a trap!',
                'description': 'Enemy Ships in Sector 47!'
            }}, status=403)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitors/{}/dialogues/{}'.format(self.monitor_id, dialogue_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Lorem ipsum')
        self.assertEqual(response.json['data']['description'], 'Lorem ipsum dolor sit amet')
        self.assertEqual(response.json['data']['dateSubmitted'], datetime.now(TZ).isoformat())

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_monitor_owner_patch_dialogue_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        dialogue_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/credentials?acc_token={}'.format(self.monitor_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.patch_json(
            '/monitors/{}/dialogues/{}?acc_token={}'.format(self.monitor_id, dialogue_id, tender_owner_token),
            {'data': {
                'answer': 'Gotcha',
            }})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_tender_owner_patch_dialogue_by_monitor_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/credentials?acc_token={}'.format(self.monitor_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        dialogue_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/dialogues/{}?acc_token={}'.format(self.monitor_id, dialogue_id, self.monitor_token),
            {'data': {
                'title': 'It’s a trap!',
                'description': 'Enemy Ships in Sector 47!',
                'answer': 'The Force will be with you. Always.'
            }}, status=200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitors/{}/dialogues/{}'.format(self.monitor_id, dialogue_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Lorem ipsum')
        self.assertEqual(response.json['data']['description'], 'Lorem ipsum dolor sit amet')
        self.assertEqual(response.json['data']['answer'], 'The Force will be with you. Always.')
        self.assertEqual(response.json['data']['dateSubmitted'], datetime.now(TZ).isoformat())

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_tender_owner_patch_dialogue_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/credentials?acc_token={}'.format(self.monitor_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitors/{}/dialogues?acc_token={}'.format(self.monitor_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        dialogue_id = response.json['data']['id']

        response = self.app.patch_json(
            '/monitors/{}/dialogues/{}?acc_token={}'.format(self.monitor_id, dialogue_id, self.monitor_token),
            {'data': {
                'title': 'It’s a trap!',
                'description': 'Enemy Ships in Sector 47!',
                'answer': 'The Force will be with you. Always.'
            }}, status=403)
        self.assertEqual(response.content_type, 'application/json')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitorDialogueResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
