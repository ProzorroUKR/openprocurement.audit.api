# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from hashlib import sha512

from openprocurement.audit.api.utils import get_now

from freezegun import freeze_time

from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin


@freeze_time('2018-01-01T11:00:00+02:00')
class BaseLiabilityTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(BaseLiabilityTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()

        self.tender_owner_token = "1234qwerty"
        monitoring = self.db.get(self.monitoring_id)
        monitoring.update(tender_owner="broker", tender_owner_token=self.tender_owner_token)
        self.db.save(monitoring)

    def create_active_monitoring(self, **kwargs):
        self.create_monitoring(**kwargs)
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": get_now().isoformat()
                },
                "status": "active",
            }}
        )

        # get credentials for tha monitoring owner
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        with mock.patch('openprocurement.audit.monitoring.validation.TendersClient') as mock_api_client:
            mock_api_client.return_value.extract_credentials.return_value = {
                'data': {'tender_token': sha512(b'tender_token').hexdigest()}
            }
            response = self.app.patch_json(
                '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
            )
        self.tender_owner_token = response.json['access']['token']

    def create_addressed_monitoring(self, **kwargs):
        self.create_active_monitoring(**kwargs)
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "description": "Some text",
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType", "corruptionAwarded"],
                },
                "status": "addressed",
            }}
        )
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

    def create_monitoring_with_elimination(self, **kwargs):
        self.create_addressed_monitoring(**kwargs)
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "description": "It's a minimal required elimination report",
                "documents": [
                    {
                        'title': 'lorem.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ]
            }},
        )
        self.elimination = response.json["data"]

    def post_eliminationResolution(self):
        self.create_monitoring_with_elimination()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": {
                    "result": "partly",
                    "resultByType": {
                        "corruptionProcurementMethodType": "eliminated",
                        "corruptionAwarded": "not_eliminated",
                    },
                    "description": "Do you have spare crutches?",
                    "documents": [
                        {
                            'title': 'sign.p7s',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/pkcs7-signature',
                        }
                    ]
                },
            }},
        )


class MonitoringLiabilityResourceTest(BaseLiabilityTest):

    def test_fail_liability_before_eliminationResolution(self):
        self.create_monitoring_with_elimination()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.put_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
            }},
            status=422
        )
        self.assertEqual(
            response.json["errors"],
            [{'description': "Can't post before eliminationResolution is published.",
              'location': 'body', 'name': 'liability'}]
        )

    def test_fail_patch_liability_before_added(self):
        self.post_eliminationResolution()

        response = self.app.patch_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
            }},
            status=404
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json["errors"],
            [{'location': 'body', 'name': 'data', 'description': 'Liability not found'}]
        )

    def test_fail_liability_none(self):
        self.post_eliminationResolution()

        self.app.authorization = None
        self.app.put_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
            }},
            status=403
        )

    def test_success_liability_minimum(self):
        self.post_eliminationResolution()

        response = self.app.put_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
            }},
        )
        self.assertEqual(
            response.json["data"],
            {'reportNumber': '1234567890',
             'datePublished': '2018-01-01T11:00:00+02:00'}
        )

    def test_success_liability_with_document(self):
        self.post_eliminationResolution()

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.put_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
                'documents': [
                    {
                        'title': 'lorem.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ]
            }},
        )
        self.assertEqual(len(response.json["data"]["documents"]), 1)
        document = response.json["data"]["documents"][0]
        self.assertEqual(
            set(document.keys()),
            {
                'hash', 'author', 'format', 'url',
                'title', 'datePublished', 'dateModified', 'id',
            }
        )


class MonitoringLiabilityPostedResourceTest(BaseLiabilityTest):

    def setUp(self):
        super(MonitoringLiabilityPostedResourceTest, self).setUp()
        self.post_eliminationResolution()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.put_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
                'documents': [
                    {
                        'title': 'first.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }
                ]
            }},
        )
        self.document_id = response.json["data"]["documents"][0]["id"]

    def test_get_liability(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(
            '/monitorings/{}/liability'.format(self.monitoring_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["reportNumber"], '1234567890')

    def test_success_update_liability(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {"data": {
                "proceeding": {
                    "type": "sas",
                    "dateProceedings": get_now().isoformat(),
                    "proceedingNumber": "somenumber",
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("proceeding", response.json["data"])
        proceeding = response.json["data"]["proceeding"]
        self.assertIn(proceeding["type"], "sas")
        self.assertEqual(proceeding["proceedingNumber"], "somenumber")

        response = self.app.patch_json(
            '/monitorings/{}/liability'.format(self.monitoring_id),
            {"data": {
                "proceeding": {
                    "type": "court",
                    "dateProceedings": get_now().isoformat(),
                    "proceedingNumber": "somenumber",
                }
            }},
            status=403
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json["errors"],
            [{"location": "body", "name": "data", "description": "Can't post another proceeding."}]
        )

    def test_fail_patch_liability(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}/liability?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {
                "proceeding": {
                    "type": "some_type",
                    "proceedingNumber": "somenumber",
                }
            }},
            status=422
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json["errors"][0]["description"],
            {'type': ["Value must be one of ['sas', 'court']."], 'dateProceedings': ['This field is required.']},
        )

    def test_fail_update_liability(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.put_json(
            '/monitorings/{}/liability?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'description': 'Another description',
            }},
            status=403
        )
        self.assertEqual(
            response.json["errors"],
            [
                {
                    "location": "body",
                    "name": "data",
                    "description": "Can't post another liability."
                }
            ]
        )

    def test_success_post_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/liability/documents?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {'data': {
                'title': 'lorem.doc',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/msword',
            }},
        )
        self.assertEqual(
            set(response.json["data"].keys()),
            {'hash', 'author', 'format', 'url', 'title', 'datePublished', 'dateModified', 'id'}
        )

    def test_success_put_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            'title': 'another.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/json',
        }
        response = self.app.put_json(
            '/monitorings/{}/liability/documents/{}?acc_token={}'.format(
                self.monitoring_id, self.document_id, self.tender_owner_token
            ),
            {'data': request_data},
        )
        self.assertEqual(
            set(response.json["data"].keys()),
            {'hash', 'author', 'format', 'url', 'title', 'datePublished', 'dateModified', 'id'}
        )
        data = response.json["data"]
        self.assertEqual(data["id"], self.document_id)
        self.assertEqual(data["format"], request_data["format"])
        self.assertEqual(data["title"], request_data["title"])

    def test_success_patch_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            'title': 'another.doc',
            'url': self.generate_docservice_url(),
            'format': 'application/json',
        }
        response = self.app.patch_json(
            '/monitorings/{}/liability/documents/{}?acc_token={}'.format(
                self.monitoring_id, self.document_id, self.tender_owner_token
            ),
            {'data': request_data},
        )
        self.assertEqual(
            set(response.json["data"].keys()),
            {'hash', 'author', 'format', 'url', 'title', 'datePublished', 'dateModified', 'id'}
        )
        data = response.json["data"]
        self.assertEqual(data["id"], self.document_id)
        self.assertEqual(data["format"], request_data["format"])
        self.assertEqual(data["title"], request_data["title"])
        self.assertNotEqual(data["url"], request_data["url"])
