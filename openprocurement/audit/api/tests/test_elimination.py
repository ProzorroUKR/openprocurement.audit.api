from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
from freezegun import freeze_time
from datetime import datetime
from hashlib import sha512
import unittest
import mock


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitoringEliminationBaseTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringEliminationBaseTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'

    def create_satisfied_monitoring(self):
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": datetime.now().isoformat()
                },
                "status": "active",
            }}
        )
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

        # get credentials for tha monitoring owner
        self.app.authorization = ('Basic', (self.broker_token, ''))
        with mock.patch('openprocurement.audit.api.validation.TendersClient') as mock_api_client:
            mock_api_client.return_value.extract_credentials.return_value = {
                'data': {'tender_token': sha512('tender_token').hexdigest()}
            }
            response = self.app.patch_json(
                '/monitorings/{}/credentials?acc_token={}'.format(self.monitoring_id, 'tender_token')
            )
        self.tender_owner_token = response.json['access']['token']

    def create_monitoring_with_elimination(self):
        self.create_satisfied_monitoring()
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

    def create_monitoring_with_resolution(self):
        self.create_monitoring_with_elimination()
        self.app.authorization = ('Basic', (self.sas_token, ''))
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


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitoringEliminationResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(MonitoringEliminationResourceTest, self).setUp()
        self.create_satisfied_monitoring()

    def test_get_elimination(self):
        self.app.get(
            '/monitorings/{}/eliminationReport'.format(self.monitoring_id),
            status=403
        )

    def test_patch_elimination(self):
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {"description": "One pint, two pint, three pint, four,"}},
            status=403
        )

    def test_patch_sas_elimination(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}/eliminationReport'.format(self.monitoring_id),
            {"data": {"description": "One pint, two pint, three pint, four,"}},
            status=403
        )

    def test_success_put(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            "description": "Five pint, six pint, seven pint, flour.",
            "dateCreated": "1988-07-11T15:53:06.068598+03:00",
            "dateModified": "1988-07-11T15:53:06.068598+03:00",
            "documents": [
                {
                    'title': 'lorem.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }
            ],
        }
        response = self.app.put_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
        )
        self.assertEqual(response.status_code, 200)

        # get monitoring
        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(data["description"], request_data["description"])
        self.assertEqual(data["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(data["dateModified"], "2018-01-01T11:00:00+02:00")
        self.assertNotIn("resolution", data)
        self.assertEqual(len(data["documents"]), 1)

    def test_fail_update_resolution(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
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
        }
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )


class UpdateEliminationResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(UpdateEliminationResourceTest, self).setUp()
        self.create_monitoring_with_elimination()

    def test_forbidden_sas_patch(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
            "description": "I'm gonna change this",
            "documents": [],
        }
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
            status=403
        )

    def test_forbidden_without_token_patch(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            "description": "I'm gonna change this",
            "documents": [],
        }
        self.app.patch_json(
            '/monitorings/{}/eliminationReport'.format(self.monitoring_id),
            {"data": request_data},
            status=403
        )

    def test_success_minimal_patch(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            "description": "I'm gonna change this",
        }
        response = self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
        )
        self.assertEqual(response.json["data"]["description"], request_data["description"])

    @freeze_time('2018-01-02T11:30:00+02:00')
    def test_success_patch(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            "description": "I'm gonna change this",
            "documents": [
                {
                    'title': 'and this.doc',
                    'url': self.generate_docservice_url() + "#1",
                    'hash': 'md5:' + '1' * 32,
                    'format': 'application/json',
                }
            ],
        }
        response = self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": request_data},
        )
        self.assertEqual(response.status_code, 200)

        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(data["description"], request_data["description"])
        self.assertEqual(data["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(data["dateModified"], "2018-01-02T11:30:00+02:00")
        self.assertEqual(data["documents"][0]["title"], request_data["documents"][0]["title"])
        self.assertEqual(data["documents"][0]["url"], request_data["documents"][0]["url"])
        self.assertEqual(data["documents"][0]["hash"], request_data["documents"][0]["hash"])
        self.assertEqual(data["documents"][0]["format"], request_data["documents"][0]["format"])
        self.assertNotIn("resolution", data)

    def test_forbidden_sas_post_document(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        self.app.post_json(
            '/monitorings/{}/eliminationReport/documents?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": document},
            status=403
        )

    def test_forbidden_without_token_post_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        self.app.post_json(
            '/monitorings/{}/eliminationReport/documents'.format(self.monitoring_id),
            {"data": document},
            status=403
        )

    def test_success_post_document(self):
        # dateModified
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json["data"]["dateModified"], '2018-01-01T11:00:00+02:00')

        self.app.authorization = ('Basic', (self.broker_token, ''))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        post_time = '2018-01-13T13:35:00+02:00'
        with freeze_time(post_time):
            response = self.app.post_json(
                '/monitorings/{}/eliminationReport/documents?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
                {"data": document},
            )
        self.assertEqual(response.status_code, 201)

        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(len(data["documents"]), 2)
        self.assertEqual(data["documents"][1]["title"], document["title"])

        # dateModified
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json["data"]["dateModified"], post_time)

    def test_success_patch_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        document = {
            'title': 'another.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        doc_to_update = self.elimination["documents"][0]

        response = self.app.patch_json(
            '/monitorings/{}/eliminationReport/documents/{}?acc_token={}'.format(
                self.monitoring_id, doc_to_update["id"], self.tender_owner_token
            ),
            {"data": document},
        )
        self.assertEqual(response.status_code, 200)

        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(len(data["documents"]), 1)
        self.assertEqual(data["documents"][0]["id"], doc_to_update["id"])
        self.assertEqual(data["documents"][0]["title"], document["title"])

    def test_success_put_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        document = {
            'title': 'my_new_file.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'text/css',
        }
        doc_to_update = self.elimination["documents"][0]

        response = self.app.put_json(
            '/monitorings/{}/eliminationReport/documents/{}?acc_token={}'.format(
                self.monitoring_id, doc_to_update["id"], self.tender_owner_token
            ),
            {"data": document},
        )
        self.assertEqual(response.status_code, 200)

        self.app.authorization = None
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(len(data["documents"]), 2)

        response = self.app.get(
            '/monitorings/{}/eliminationReport/documents/{}'.format(
                self.monitoring_id, doc_to_update["id"]
            ),
            {"data": document},
        )
        self.assertEqual(response.status_code, 200)
        resp_data = response.json["data"]
        self.assertEqual(resp_data["title"], document["title"])
        # self.assertEqual(resp_data["url"], document["url"])
        self.assertEqual(resp_data["format"], document["format"])

    def test_fail_update_resolution_wo_result_by_type(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
            "result": "partly",
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )
        self.assertEqual(response.json["errors"][0]["description"],
                         {"resultByType": ["This field is required."]})

    def test_fail_update_resolution_wrong_result_by_type(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionChanges": "eliminated",
            }
        }
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )

    def test_fail_update_resolution_wrong_result_by_type_value(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
            "result": "partly",
            "resultByType": {
                "corruptionProcurementMethodType": "eliminated",
                "corruptionAwarded": "Nope",
            }
        }
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )

    def test_success_update_resolution(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
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
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        resolution = response.json["data"]["eliminationResolution"]

        self.assertEqual(resolution["result"], request_data["result"])
        self.assertEqual(resolution["resultByType"], request_data["resultByType"])
        self.assertEqual(resolution["description"], request_data["description"])
        self.assertEqual(resolution["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(len(resolution["documents"]), len(request_data["documents"]))

    def test_fail_change_status(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "completed",
            }},
            status=403
        )
        self.assertEqual(
            response.json["errors"],
            [{
                'description': "Can't change status to completed before elimination period ends.",
                'location': 'body',
                'name': 'data'
            }]
        )


@freeze_time('2018-01-01T12:00:00.000000+03:00')
class ResolutionMonitoringResourceTest(MonitoringEliminationBaseTest):

    def setUp(self):
        super(ResolutionMonitoringResourceTest, self).setUp()
        self.create_monitoring_with_resolution()

    def test_success_change_report(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {"description": "I want to change this description"}},
        )
        self.assertEqual(response.status_code, 200)

    @freeze_time('2018-01-20T12:00:00.000000+03:00')
    def test_success_change_status(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "completed",
            }},
        )
        self.assertEqual(response.json["data"]["status"], "completed")

        # can't update resolution
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "eliminationResolution": {
                    "result": "completely",
                },
            }},
            status=422
        )

        # can't update elimination report
        self.app.authorization = ('Basic', (self.broker_token, ''))
        self.app.patch_json(
            '/monitorings/{}/eliminationReport?acc_token={}'.format(self.monitoring_id, self.tender_owner_token),
            {"data": {"description": "I want to change this description"}},
            status=422
        )


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitoringEliminationResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
