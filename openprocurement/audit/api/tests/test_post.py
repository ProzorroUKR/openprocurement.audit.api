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


@freeze_time('2018-01-01T12:00:00+02:00')
class MonitoringPostResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringPostResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
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

    def test_post_create_required_fields(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {}}, status=422)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {('body', 'title'), ('body', 'description')},
            get_errors_field_names(response, 'This field is required.'))

    @freeze_time('2018-01-02T12:30:00+02:00')
    def test_post_create_by_monitoring_owner(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))

        # check initial date modified
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['dateModified'], '2018-01-01T12:00:00+02:00')

        request_data = {
            'title': 'Lorem ipsum',
            'description': 'Lorem ipsum dolor sit amet',
            'documents': [{
                'title': 'lorem.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }]
        }
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': request_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}'.format(self.monitoring_id, post_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], request_data["title"])
        self.assertEqual(response.json['data']['description'], request_data['description'])
        self.assertEqual(response.json['data']['author'], 'monitoring_owner')
        self.assertEqual(len(response.json['data']['documents']), 1)
        self.assertNotEqual(response.json['data']['documents'][0]['url'], request_data["documents"][0]['url'])

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['dateModified'], '2018-01-02T12:30:00+02:00')

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_post_create_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']

        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}'.format(self.monitoring_id, post_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Lorem ipsum')
        self.assertEqual(response.json['data']['description'], 'Lorem ipsum dolor sit amet')
        self.assertEqual(response.json['data']['author'], 'tender_owner')

    def test_monitoring_owner_answer_post_by_monitoring_owner(self):
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'It’s a trap!',
                'description': 'Enemy Ships in Sector 47!',
                'relatedPost': post_id
            }}, status=422)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('restkit.Resource.request')
    def test_monitoring_credentials_tender_owner(self, mock_request):
        mock_request.return_value = mock.MagicMock(
            status_int=200,
            body_string=lambda: json.dumps({'data': {'tender_token': sha512('tender_token').hexdigest()}})
        )

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )
        self.assertIn("access", response.json)
        self.assertIn("token", response.json["access"])

        self.assertIs(mock_request.called, True)
        args, kwargs = mock_request.call_args
        self.assertEqual(
            kwargs["path"],
            '/api/2.0/tenders/{}/extract_credentials'.format(self.initial_data["tender_id"])
        )

        self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'another_token'),
            status=403
        )

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_monitoring_owner_answer_post_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet',
                'documents': [{
                    'title': 'lorem.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }]
            }})
        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Gotcha',
                'relatedPost': post_id
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_tender_owner_answer_post_by_monitoring_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'Enemy Ships in Sector 47!',
            }})
        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id, post_id),
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'The Force will be with you. Always.',
            }}, status=201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}'.format(self.monitoring_id, post_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'It\'s a trap!')
        self.assertEqual(response.json['data']['description'], 'The Force will be with you. Always.')

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_tender_owner_answer_post_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        post_id = response.json['data']['id']

        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'It’s a trap!',
                'description': 'The Force will be with you. Always.',
                'relatedPost': post_id
            }}, status=422)
        self.assertEqual(response.content_type, 'application/json')

@freeze_time('2018-01-01T12:00:00.000000+03:00')
class AddressedMonitoringPostResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(AddressedMonitoringPostResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                }
            }})
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                },
                "status": "declined",
            }})

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_post_create_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_post_answer_by_monitoring_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_token, ''))

        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet',
                'relatedPost': post_id
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_post_create_by_tender_owner_multiple(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512('tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }}, status=403)

    def test_post_create_by_monitoring_owner(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }}, status=403)
        self.assertEqual(response.status_code, 403)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MonitoringPostResourceTest))
    suite.addTest(unittest.makeSuite(AddressedMonitoringPostResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')