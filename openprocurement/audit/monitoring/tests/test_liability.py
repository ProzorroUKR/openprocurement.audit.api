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

    def test_fail_patch_liability_before_added(self):
        self.post_eliminationResolution()

        response = self.app.patch_json(
            '/monitorings/{}/liabilities/some_id'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
            }},
            status=404
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json["errors"],
            [{'location': 'url', 'name': 'liability_id', 'description': 'Not Found'}]
        )

    def test_fail_liability_none(self):
        self.post_eliminationResolution()

        self.app.authorization = None
        self.app.post_json(
            '/monitorings/{}/liabilities'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
            }},
            status=403
        )

    def test_fail_liability_not_in_valid_monitoring_status(self):
        self.create_active_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/liabilities'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
                'legislation': {
                    'article': ['8.10'],
                }
            }},
            status=403,
        )
        self.assertEqual(
            response.json["errors"],
            [
                {
                    "location": "body",
                    "name": "data",
                    "description": "Liability can\'t be added to monitoring in current (active) status",
                },
            ],
        )

    def test_success_liability_minimum(self):
        self.post_eliminationResolution()

        response = self.app.post_json(
            '/monitorings/{}/liabilities'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
                'legislation': {
                    'article': ['8.10'],
                }
            }},
        )
        laibilty_id = response.json["data"]["id"]
        self.assertEqual(
            response.json["data"],
            {
                'id': laibilty_id,
                'reportNumber': '1234567890',
                'datePublished': '2018-01-01T11:00:00+02:00',
                'legislation': {
                    'version': '2020-11-21',
                    'article': ['8.10'],
                    'type': 'NATIONAL_LEGISLATION',
                    'identifier': {
                        'id': '8073-X',
                        'legalName': 'Кодекс України про адміністративні правопорушення',
                        'uri': 'https://zakon.rada.gov.ua/laws/show/80731-10#Text',
                    }
                }
            }
        )

    def test_success_liability_with_document(self):
        self.post_eliminationResolution()

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/liabilities'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
                'legislation': {
                    'version': '13.08.2020',
                    'article': ['8.10'],
                    'type': 'NATIONAL_LEGISLATION',
                    'identifier': {
                        'id': '8073-X',
                        'legalName': 'Кодекс України про адміністративні правопорушення',
                        'uri': 'https://zakon.rada.gov.ua/laws/show/80731-10#Text',
                    }
                },
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
        response = self.app.post_json(
            '/monitorings/{}/liabilities'.format(self.monitoring_id),
            {'data': {
                'reportNumber': '1234567890',
                'legislation': {
                    'version': '13.08.2020',
                    'article': ['8.10'],
                    'type': 'NATIONAL_LEGISLATION',
                    'identifier': {
                        'id': '8073-X',
                        'legalName': 'Кодекс України про адміністративні правопорушення',
                        'uri': 'https://zakon.rada.gov.ua/laws/show/80731-10#Text',
                    }
                },
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
        self.liability_id = response.json["data"]["id"]
        self.document_id = response.json["data"]["documents"][0]["id"]

    def test_get_liability(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(
            '/monitorings/{}/liabilities/{}'.format(self.monitoring_id, self.liability_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json["data"]["reportNumber"], '1234567890')

    def test_success_update_liability(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}/liabilities/{}'.format(self.monitoring_id, self.liability_id),
            {'data': {
                'proceeding': {
                    'dateProceedings': get_now().isoformat(),
                    'proceedingNumber': 'somenumber',
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("proceeding", response.json["data"])
        proceeding = response.json["data"]["proceeding"]
        self.assertEqual(proceeding["proceedingNumber"], "somenumber")

        response = self.app.patch_json(
            '/monitorings/{}/liabilities/{}'.format(self.monitoring_id, self.liability_id),
            {"data": {
                "proceeding": {
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
            '/monitorings/{}/liabilities/{}'.format(self.monitoring_id, self.liability_id),
            {"data": {
                "proceeding": {
                    "proceedingNumber": "somenumber",
                }
            }},
            status=422
        )
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json["errors"][0]["description"],
            {'dateProceedings': ['This field is required.']},
        )

    def test_success_post_document(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/monitorings/{}/liabilities/{}/documents'.format(
                self.monitoring_id, self.liability_id
            ),
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
            '/monitorings/{}/liabilities/{}/documents/{}'.format(
                self.monitoring_id, self.liability_id, self.document_id
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
            '/monitorings/{}/liabilities/{}/documents/{}'.format(
                self.monitoring_id, self.liability_id, self.document_id
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