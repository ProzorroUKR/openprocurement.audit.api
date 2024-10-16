# -*- coding: utf-8 -*-
import json
import unittest
from hashlib import sha512
from unittest import mock
from freezegun import freeze_time

from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


@freeze_time('2018-01-01T12:00:00+02:00')
class MonitoringPostResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringPostResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
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

    def test_post_get_empty_list(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}/posts'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 0)

    def test_post_create_required_fields(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {}}, status=422)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            {
                ('body', 'title'),
                ('body', 'description')
            },
            set(get_errors_field_names(response, 'This field is required.'))
        )

    @freeze_time('2018-01-02T12:30:00+02:00')
    def test_post_create_by_monitoring_owner(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        # check initial date modified
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['dateModified'], '2018-01-01T12:00:00+02:00')

        request_doc_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        request_data = {
            'title': 'Lorem ipsum',
            'description': 'Lorem ipsum dolor sit amet',
            'documents': [request_doc_data]
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
        doc_data = response.json['data']['documents'][0]
        self.assertEqual(
            doc_data['url'].split("Signature")[0],
            request_doc_data['url'].split("Signature")[0],
        )

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['dateModified'], '2018-01-02T12:30:00+02:00')

        # update  document
        doc_hash = '1' * 32
        request_data = {
            'title': 'sign-1.p7s',
            'url': self.generate_docservice_url(doc_hash=doc_hash),
            'format': 'application/json',
            'hash': 'md5:' + doc_hash,
        }
        response = self.app.put_json(
            '/monitorings/{}/posts/{}/documents/{}'.format(
                self.monitoring_id,
                post_id,
                doc_data["id"]
            ),
            {'data': request_data},
        )
        self.assertEqual(response.json["data"]["title"], request_data["title"])
        self.assertEqual(
            response.json["data"]["url"].split("Signature")[0],
            request_data["url"].split("Signature")[0],
        )
        self.assertEqual(response.json["data"]["format"], request_data["format"])
        self.assertEqual(response.json["data"]["hash"], request_data["hash"])

        # update doc data
        request_data = {
            'title': 'sign-2.p7s',
            'url': self.generate_docservice_url(),
            'format': 'application/pkcs7-signature',
            'hash': 'md5:' + '2' * 32,
        }
        response = self.app.patch_json(
            '/monitorings/{}/posts/{}/documents/{}'.format(
                self.monitoring_id,
                post_id,
                doc_data["id"]
            ),
            {'data': request_data},
        )
        self.assertEqual(response.json["data"]["title"], request_data["title"])
        self.assertEqual(response.json["data"]["format"], request_data["format"])
        self.assertNotEqual(
            response.json["data"]["url"].split("Signature")[0],
            request_data["url"].split("Signature")[0],
        )
        self.assertNotEqual(response.json["data"]["hash"], request_data["hash"])

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_post_create_by_tender_owner(self, mock_api_client):
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

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'It’s a trap!',
                'description': 'Enemy Ships in Sector 47!',
                'relatedPost': post_id
            }}, status=422)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            ('body', 'posts', 'relatedPost'),
            next(get_errors_field_names(response, 'relatedPost can\'t have the same author.')))

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_monitoring_credentials_tender_owner(self, client_class_mock):
        client_class_mock.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )
        self.assertIn("access", response.json)
        self.assertIn("token", response.json["access"])

        registry = self.app.app.registry
        client_class_mock.assert_called_once_with(
            registry.api_token,
            host_url=registry.api_server,
            api_version=registry.api_version,
        )
        client_class_mock.return_value.extract_credentials.assert_called_once_with(self.initial_data["tender_id"])

        self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'another_token'),
            status=403
        )

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_monitoring_owner_answer_post_by_tender_owner(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
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

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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

        answer_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}'.format(self.monitoring_id, answer_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'Lorem ipsum')
        self.assertEqual(response.json['data']['description'], 'Gotcha')
        self.assertEqual(response.json['data']['relatedPost'], post_id)

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_monitoring_owner_answer_post_by_tender_owner_multiple(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
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

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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

        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Gotcha',
                'relatedPost': post_id
            }}, status=422)
        self.assertEqual(
            ('body', 'posts', 'relatedPost'),
            next(get_errors_field_names(response, 'relatedPost must be unique.')))

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_monitoring_owner_answer_post_for_not_unique_id(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }
        with mock.patch('openprocurement.audit.monitoring.models.uuid4', mock.Mock(return_value=mock.Mock(hex='f'*32))):
            self.app.post_json(
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

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
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
            }}, status=422)

        self.assertEqual(
            ('body', 'relatedPost'),
            next(get_errors_field_names(response, 'relatedPost can\'t be a link to more than one post.')))

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_tender_owner_answer_post_by_monitoring_owner(self, mock_api_client):
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
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'Enemy Ships in Sector 47!',
            }})
        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id, post_id),
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'The Force will be with you. Always.',
                'relatedPost': post_id
            }}, status=201)
        self.assertEqual(response.content_type, 'application/json')

        answer_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}'.format(self.monitoring_id, answer_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['title'], 'It\'s a trap!')
        self.assertEqual(response.json['data']['description'], 'The Force will be with you. Always.')
        self.assertEqual(response.json['data']['relatedPost'], post_id)

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_tender_owner_answer_post_by_tender_owner(self, mock_api_client):
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
        self.assertEqual(
            ('body', 'posts', 'relatedPost'),
            next(get_errors_field_names(response, 'relatedPost can\'t have the same author.')))

    def test_answer_to_non_existent_question(self):
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Gotcha',
                'relatedPost': 'some_non_existent_id'
            }}, status=422)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            ('body', 'relatedPost'),
            next(get_errors_field_names(response, 'relatedPost should be one of posts of current monitoring.')))

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_two_answers_in_a_row(self, mock_api_client):
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
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'Enemy Ships in Sector 47!',
            }})
        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id, post_id),
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'The Force will be with you. Always.',
                'relatedPost': post_id
            }}, status=201)
        self.assertEqual(response.content_type, 'application/json')

        answer_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'It\'s a trap!',
                'description': 'Enemy Ships in Sector 47!',
                'relatedPost': answer_id
            }}, status=422)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            ('body', 'relatedPost'),
            next(get_errors_field_names(response, 'relatedPost can\'t be have relatedPost defined.')))

    def test_dialogue_party_create(self):
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

        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
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

        post_id = response.json['data']['id']

        response = self.app.get('/monitorings/{}/posts/{}'.format(self.monitoring_id, post_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['relatedParty'], party_id)

    def test_dialogue_party_create_party_id_not_exists(self):
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

        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
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

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'relatedParty'),
            next(get_errors_field_names(response, 'relatedParty should be one of parties.')))

    def test_restricted_visibility(self):
        self.create_monitoring(parties=[self.initial_party], restricted_config=True)
        self.app.patch_json(
            f'/monitorings/{self.monitoring_id}',
            {'data': {
                "status": "active",
                "decision": {
                    "date": "2015-05-10T23:11:39.720908+03:00",
                    "description": "text",
                }
            }}
        )
        request_doc_data = {
            'title': 'lorem.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        request_data = {
            'title': 'Lorem ipsum',
            'description': 'Lorem ipsum dolor sit amet',
            'documents': [request_doc_data]
        }
        self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': request_data}
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["posts"][0]["title"], "Lorem ipsum")
        self.assertEqual(response.json['data']["posts"][0]["description"], "Lorem ipsum dolor sit amet")
        self.assertEqual(response.json['data']["posts"][0]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["posts"][0]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["posts"][0]["title"], "Lorem ipsum")
        self.assertEqual(response.json['data']["posts"][0]["description"], "Lorem ipsum dolor sit amet")
        self.assertEqual(response.json['data']["posts"][0]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["posts"][0]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["posts"][0]["description"], "Приховано")
        self.assertEqual(response.json['data']["posts"][0]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["posts"][0]["documents"][0]["url"], "Приховано")


@freeze_time('2018-01-01T12:00:00.000000+03:00')
class DeclinedMonitoringPostResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(DeclinedMonitoringPostResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_post_create_by_tender_owner(self, mock_api_client):
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
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_post_answer_by_monitoring_owner(self, mock_api_client):
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
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

        post_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet',
                'relatedPost': post_id
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_post_create_by_tender_owner_multiple(self, mock_api_client):
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(b'tender_token').hexdigest()}
        }

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.patch_json(
            '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
        )

        tender_owner_token = response.json['access']['token']

        # add first
        response = self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content_type, 'application/json')
        post_id = response.json["data"]["id"]

        # add second
        self.app.post_json(
            '/monitorings/{}/posts?acc_token={}'.format(self.monitoring_id, tender_owner_token),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }}, status=403)

        # add a document to the post
        response = self.app.post_json(
            '/monitorings/{}/posts/{}/documents?acc_token={}'.format(self.monitoring_id, post_id, tender_owner_token),
            {'data': {
                'title': 'ipsum.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }})
        self.assertEqual(response.status_code, 201)

    def test_post_create_by_monitoring_owner(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }}, status=403)
        self.assertEqual(response.status_code, 403)

    @freeze_time('2018-01-20T12:00:00.000000+03:00')
    def test_post_create_in_non_allowed_status(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                'status': 'closed',
            }})
        self.assertEqual(response.status_code, 200)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/posts'.format(self.monitoring_id),
            {'data': {
                'title': 'Lorem ipsum',
                'description': 'Lorem ipsum dolor sit amet'
            }}, status=403)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            ('body', 'data'),
            next(get_errors_field_names(response, 'Can\'t add post in current closed monitoring status.'))
        )
