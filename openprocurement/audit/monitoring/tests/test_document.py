# -*- coding: utf-8 -*-
import unittest
from hashlib import sha512
from unittest import mock

from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.test_elimination import MonitoringEliminationBaseTest
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


class MonitoringDecisionDocumentResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringDecisionDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentType': 'notice',
            'id': '0' * 32
        }
        self.test_monitoring_activation_data = {
            "status": "active",
            "decision": {
                "date": "2015-05-10T23:11:39.720908+03:00",
                "description": "text",
                "documents": [self.test_docservice_document_data]
            }
        }

    def test_document_get_single(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_id = response.json['data']['decision']['documents'][-1]['id']

        response = self.app.get('/monitorings/{}/decision/documents/{}'.format(self.monitoring_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])
        self.assertEqual(document_data["documentType"], "notice")

    def test_document_get_list(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitorings/{}/decision/documents'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    def test_document_download(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']['decision']['documents'][-1]
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/decision/documents/{}?download=some_id'.format(
            self.monitoring_id, document_id), status=404)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/decision/documents/{}?download={}'.format(
            self.monitoring_id, document_id, key))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    def test_document_upload(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {'decision': self.test_monitoring_activation_data['decision']}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/decision/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    def test_document_upload_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/decision/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data}, status=403)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'data'),
            next(get_errors_field_names(response, 'Can\'t add document in current active monitoring status.')))

class MonitoringPostActiveDocumentResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringPostActiveDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                    "documents": [self.test_docservice_document_data]
                }
            }}
        )
        self.post_data = {
            'title': 'Lorem ipsum',
            'description': 'Lorem ipsum dolor sit amet',
            'documents': [self.test_docservice_document_data]
        }

    def test_document_get_single(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']
        document_id = response.json['data']['documents'][-1]['id']

        response = self.app.get('/monitorings/{}/posts/{}/documents/{}'.format(self.monitoring_id, post_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    def test_document_get_list(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}/documents'.format(self.monitoring_id, post_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    def test_document_download(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']
        document_data = response.json['data']['documents'][-1]
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/posts/{}/documents/{}?download=some_id'.format(
            self.monitoring_id, post_id, document_id), status=404)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/posts/{}/documents/{}?download={}'.format(
            self.monitoring_id, post_id, document_id, key))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    def test_document_upload(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.post_json('/monitorings/{}/posts/{}/documents'.format(
            self.monitoring_id, post_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    def test_document_upload_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "addressed",
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType"],
                }
            }}
        )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        response = self.app.post_json('/monitorings/{}/posts/{}/documents'.format(
            self.monitoring_id, post_id),
            {'data': self.test_docservice_document_data}, status=403)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

class MonitoringPostAddressedDocumentResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringPostAddressedDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                    "documents": [self.test_docservice_document_data]
                }
            }}
        )
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "conclusion": {
                    "description": "Some text",
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType", "corruptionAwarded"],
                    "documents": [self.test_docservice_document_data]
                },
                "status": "addressed",
            }}
        )
        self.post_data = {
            'title': 'Lorem ipsum',
            'description': 'Lorem ipsum dolor sit amet',
            'documents': [self.test_docservice_document_data]
        }

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_document_get_single(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']
        document_id = response.json['data']['documents'][-1]['id']

        response = self.app.get('/monitorings/{}/posts/{}/documents/{}'.format(self.monitoring_id, post_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_document_get_list(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}/documents'.format(self.monitoring_id, post_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_document_download(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']
        document_data = response.json['data']['documents'][-1]
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/posts/{}/documents/{}?download=some_id'.format(
            self.monitoring_id, post_id, document_id), status=404)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/posts/{}/documents/{}?download={}'.format(
            self.monitoring_id, post_id, document_id, key))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_document_upload_no_token(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.post_json('/monitorings/{}/posts/{}/documents'.format(
            self.monitoring_id, post_id),
            {'data': self.test_docservice_document_data}, status=403)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_document_upload(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        response = self.app.post_json('/monitorings/{}/posts/{}/documents?acc_token={}'.format(
            self.monitoring_id, post_id, tender_owner_token),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_document_upload_author_forbidden(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': self.post_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.post_json('/monitorings/{}/posts/{}/documents'.format(
            self.monitoring_id, post_id),
            {'data': self.test_docservice_document_data}, status=403)


class MonitoringDocumentResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.test_monitoring_activation_data = {
            "documents": [self.test_docservice_document_data],
        }

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                'status': "cancelled",
                'cancellation': {
                   "description": "text"
                }
            }})

    def test_document_get_single(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_id = response.json['data']['documents'][-1]['id']

        response = self.app.get('/monitorings/{}/documents/{}'.format(self.monitoring_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    def test_document_get_list(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitorings/{}/documents'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    def test_document_download(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']['documents'][-1]
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/documents/{}?download=some_id'.format(
            self.monitoring_id, document_id), status=404)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/documents/{}?download={}'.format(
            self.monitoring_id, document_id, key))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    def test_document_upload(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    def test_restricted_visibility(self):
        self.create_monitoring(parties=[self.initial_party], restricted_config=True)
        response = self.app.patch_json(
            f'/monitorings/{self.monitoring_id}',
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                },
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.app.post_json(
            f'/monitorings/{self.monitoring_id}/documents',
            {'data': self.test_docservice_document_data},
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["documents"][0]["url"], "Приховано")


class MonitoringCancellationDocumentResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringCancellationDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.test_monitoring_activation_data = {
            'status': "cancelled",
            'cancellation': {
                "description": "text",
                "documents": []
            }
        }

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_activation_data})

        self.end_point = '/monitorings/%s/cancellation/documents' % self.monitoring_id

    def test_get_single(self):
        response = self.app.post_json(
            '/monitorings/{}/cancellation/documents'.format(self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        document_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/cancellation/documents/{}'.format(self.monitoring_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    def test_document_get_list(self):
        response = self.app.post_json(
            '/monitorings/{}/cancellation/documents'.format(self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitorings/{}/cancellation/documents'.format(self.monitoring_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    def test_document_download(self):
        response = self.app.post_json(
            '/monitorings/{}/cancellation/documents'.format(self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/cancellation/documents/{}?download=some_id'.format(
            self.monitoring_id, document_id), status=404)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/cancellation/documents/{}?download={}'.format(
            self.monitoring_id, document_id, key))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    def test_document_upload(self):
        response = self.app.post_json('/monitorings/{}/cancellation/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')


class MonitoringEliminationResolutionDocumentResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(MonitoringEliminationResolutionDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }

        self.create_monitoring_with_resolution()

    def test_document_get_single(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        document_id = response.json['data']['id']

        response = self.app.get(
            '/monitorings/{}/eliminationResolution/documents/{}'.format(self.monitoring_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    def test_document_get_list(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(2, len(response.json['data']))

        self.assertIn('lorem.doc', [doc['title'] for doc in response.json['data']])

    def test_document_download(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
                '/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id),
                {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']
        key = document_data["url"].split('/')[-1].split('?')[0]
        document_id = document_data['id']

        response = self.app.get('/monitorings/{}/eliminationResolution/documents/{}?download=some_id'.format(
            self.monitoring_id, document_id), status=404)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {'description': 'Not Found', 'location': 'url', 'name': 'download'}
        ])

        response = self.app.get('/monitorings/{}/eliminationResolution/documents/{}?download={}'.format(
            self.monitoring_id, document_id, key))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/get/', response.location)
        self.assertIn('Signature=', response.location)
        self.assertIn('KeyID=', response.location)
        self.assertNotIn('Expires=', response.location)

    def test_document_upload(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/monitorings/{}/eliminationResolution/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    def test_patch_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            'title': 'another.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '1' * 32,
            'format': 'application/msword',
        }
        response = self.app.get('/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id))
        doc_to_update = response.json['data'][0]

        response = self.app.patch_json(
            '/monitorings/{}/eliminationResolution/documents/{}'.format(
                self.monitoring_id, doc_to_update["id"]
            ),
            {"data": request_data}
        )
        self.assertEqual(response.json["data"]["title"], request_data["title"])
        self.assertEqual(response.json["data"]["format"], request_data["format"])
        self.assertNotEqual(
            response.json["data"]["url"].split("Signature")[0],
            request_data["url"].split("Signature")[0],
        )
        self.assertNotEqual(response.json["data"]["hash"], request_data["hash"])

    def test_patch_document_forbidden(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        document = {
            'title': 'another.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '1' * 32,
            'format': 'application/msword',
        }
        response = self.app.get('/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id))
        doc_to_update = response.json['data'][0]

        self.app.patch_json(
            '/monitorings/{}/eliminationResolution/documents/{}?acc_token={}'.format(
                self.monitoring_id, doc_to_update["id"], self.tender_owner_token
            ),
            {"data": document},
            status=403
        )

    def test_put_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            'title': 'my_new_file.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'text/css',
        }
        response = self.app.get('/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id))
        doc_to_update = response.json['data'][0]

        response = self.app.put_json(
            '/monitorings/{}/eliminationResolution/documents/{}'.format(
                self.monitoring_id, doc_to_update["id"]
            ),
            {"data": request_data}
        )
        self.assertEqual(response.json["data"]["title"], request_data["title"])
        self.assertEqual(
            response.json["data"]["url"].split("Signature")[0],
            request_data["url"].split("Signature")[0],
        )
        self.assertEqual(response.json["data"]["format"], request_data["format"])
        self.assertEqual(response.json["data"]["hash"], request_data["hash"])

    def test_put_document_forbidden(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        document = {
            'title': 'my_new_file.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'text/css',
        }
        response = self.app.get('/monitorings/{}/eliminationResolution/documents'.format(self.monitoring_id))
        doc_to_update = response.json['data'][0]

        self.app.put_json(
            '/monitorings/{}/eliminationResolution/documents/{}?acc_token={}'.format(
                self.monitoring_id, doc_to_update["id"], self.tender_owner_token
            ),
            {"data": document},
            status=403
        )


class MonitoringConclusionDocumentResourceTest(BaseWebTest, DSWebTestMixin):
    def setUp(self):
        super(MonitoringConclusionDocumentResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.test_docservice_document_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                    "documents": [self.test_docservice_document_data]
                }
            }}
        )
        self.test_monitoring_addressed_data = {
            "conclusion": {
                "description": "Some text",
                "violationOccurred": True,
                "violationType": ["corruptionProcurementMethodType", "corruptionAwarded"],
                "documents": [self.test_docservice_document_data]
            },
            "status": "addressed",
        }

    def test_document_get_single(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_addressed_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_id = response.json['data']['conclusion']['documents'][-1]['id']

        response = self.app.get('/monitorings/{}/conclusion/documents/{}'.format(self.monitoring_id, document_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        document_data = response.json['data']

        self.assertEqual(document_data['title'], 'lorem.doc')
        self.assertIn('Signature=', document_data["url"])
        self.assertIn('KeyID=', document_data["url"])
        self.assertNotIn('Expires=', document_data["url"])

    def test_document_get_list(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_addressed_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.get('/monitorings/{}/conclusion/documents'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(len(response.json['data']), 1)

        document_data = response.json['data'][-1]
        self.assertEqual(document_data['title'], 'lorem.doc')

    def test_document_upload(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {'conclusion': self.test_monitoring_addressed_data['conclusion']}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/conclusion/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    def test_document_patch(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {'conclusion': self.test_monitoring_addressed_data['conclusion']}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/conclusion/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        doc_id = response.json["data"]["id"]
        old_dateModified = response.json["data"]["dateModified"]

        response = self.app.patch_json('/monitorings/{}/conclusion/documents/{}'.format(
            self.monitoring_id, doc_id),
            {'data': {'title': self.test_docservice_document_data["title"]}}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, None)

        response = self.app.patch_json('/monitorings/{}/conclusion/documents/{}'.format(
            self.monitoring_id, doc_id),
            {'data': {'title': 'lorem1.doc'}}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json["data"]["dateModified"], old_dateModified)

    def test_document_upload_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': self.test_monitoring_addressed_data})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.post_json('/monitorings/{}/conclusion/documents'.format(
            self.monitoring_id),
            {'data': self.test_docservice_document_data}, status=403)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'data'),
            next(get_errors_field_names(response, 'Can\'t add document in current addressed monitoring status.')))
