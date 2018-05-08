from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
from freezegun import freeze_time
from datetime import datetime
from hashlib import sha512
import unittest
import mock


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitorEliminationBaseTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitorEliminationBaseTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'

    def create_satisfied_monitor(self):
        self.create_monitor()
        self.app.authorization = ('Basic', (self.sas_token, ''))

        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": datetime.now().isoformat()
                },
                "status": "active",
            }}
        )
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "conclusion": {
                    "description": "Some text",
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType", "corruptionAwarded"],
                },
                "status": "addressed",
            }}
        )

        # get credentials for tha monitor owner
        self.app.authorization = ('Basic', (self.broker_token, ''))
        with mock.patch('openprocurement.audit.api.validation.TendersClient') as mock_api_client:
            mock_api_client.return_value.extract_credentials.return_value = {
                'data': {'tender_token': sha512('tender_token').hexdigest()}
            }
            response = self.app.patch_json(
                '/monitors/{}/credentials?acc_token={}'.format(self.monitor_id, 'tender_token')
            )
        self.tender_owner_token = response.json['access']['token']

    def create_monitor_with_elimination(self):
        self.create_satisfied_monitor()
        response = self.app.put_json(
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
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

    def create_monitor_with_resolution(self):
        self.create_monitor_with_elimination()
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
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


class MonitorEliminationResourceTest(MonitorEliminationBaseTest):

    def setUp(self):
        super(MonitorEliminationResourceTest, self).setUp()
        self.create_satisfied_monitor()

    def test_get_elimination(self):
        self.app.get(
            '/monitors/{}/eliminationReport'.format(self.monitor_id),
            status=403
        )

    def test_patch_elimination(self):
        self.app.patch_json(
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
            {"data": {"description": "One pint, two pint, three pint, four,"}},
            status=403
        )

    def test_patch_sas_elimination(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}/eliminationReport'.format(self.monitor_id),
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
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
            {"data": request_data},
        )
        self.assertEqual(response.status_code, 200)

        # get monitor
        self.app.authorization = None
        response = self.app.get('/monitors/{}'.format(self.monitor_id))
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
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
            status=422
        )


class UpdateEliminationResourceTest(MonitorEliminationBaseTest):

    def setUp(self):
        super(UpdateEliminationResourceTest, self).setUp()
        self.create_monitor_with_elimination()

    def test_forbidden_sas_patch(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
            "description": "I'm gonna change this",
            "documents": [],
        }
        self.app.patch_json(
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
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
            '/monitors/{}/eliminationReport'.format(self.monitor_id),
            {"data": request_data},
            status=403
        )

    def test_success_minimal_patch(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        request_data = {
            "description": "I'm gonna change this",
        }
        response = self.app.patch_json(
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
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
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }
            ],
        }
        response = self.app.patch_json(
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
            {"data": request_data},
        )
        self.assertEqual(response.status_code, 200)

        self.app.authorization = None
        response = self.app.get('/monitors/{}'.format(self.monitor_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(data["description"], request_data["description"])
        self.assertEqual(data["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(data["dateModified"], "2018-01-02T11:30:00+02:00")
        self.assertEqual(data["documents"][0]["title"], request_data["documents"][0]["title"])
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
            '/monitors/{}/eliminationReport/documents?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
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
            '/monitors/{}/eliminationReport/documents'.format(self.monitor_id),
            {"data": document},
            status=403
        )

    def test_success_post_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        document = {
            'title': 'lol.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/helloword',
        }
        response = self.app.post_json(
            '/monitors/{}/eliminationReport/documents?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
            {"data": document},
        )
        self.assertEqual(response.status_code, 201)

        self.app.authorization = None
        response = self.app.get('/monitors/{}'.format(self.monitor_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(len(data["documents"]), 2)
        self.assertEqual(data["documents"][1]["title"], document["title"])

    def test_success_update_document(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        document = {
            'title': 'another.txt',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }
        doc_to_update = self.elimination["documents"][0]
        print(doc_to_update)

        response = self.app.patch_json(
            '/monitors/{}/eliminationReport/documents/{}?acc_token={}'.format(
                self.monitor_id, doc_to_update["id"], self.tender_owner_token
            ),
            {"data": document},
        )
        self.assertEqual(response.status_code, 200)

        self.app.authorization = None
        response = self.app.get('/monitors/{}'.format(self.monitor_id))
        data = response.json["data"]["eliminationReport"]
        self.assertEqual(len(data["documents"]), 1)
        self.assertEqual(data["documents"][0]["id"], doc_to_update["id"])
        self.assertEqual(data["documents"][0]["title"], document["title"])

    def test_fail_update_resolution_wo_result_by_type(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        request_data = {
            "result": "partly",
        }
        response = self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
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
            '/monitors/{}'.format(self.monitor_id),
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
            '/monitors/{}'.format(self.monitor_id),
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
            "dateCreated": "2000-02-02T09:00:00+02:00",
            "dateModified": "1990-02-02T09:00:00+02:00",
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
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "eliminationResolution": request_data,
            }},
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitors/{}'.format(self.monitor_id))
        resolution = response.json["data"]["eliminationResolution"]

        self.assertEqual(resolution["result"], request_data["result"])
        self.assertEqual(resolution["resultByType"], request_data["resultByType"])
        self.assertEqual(resolution["description"], request_data["description"])
        self.assertEqual(resolution["dateCreated"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(resolution["dateModified"], "2018-01-01T11:00:00+02:00")
        self.assertEqual(len(resolution["documents"]), len(request_data["documents"]))

    def test_fail_change_status(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "status": "complete",
            }},
            status=422
        )


class ResolutionMonitorResourceTest(MonitorEliminationBaseTest):

    def setUp(self):
        super(ResolutionMonitorResourceTest, self).setUp()
        self.create_monitor_with_resolution()

    def test_success_change_report(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.patch_json(
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
            {"data": {"description": "I want to change this description"}},
        )
        self.assertEqual(response.status_code, 200)

    def test_success_change_status(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "status": "complete",
            }},
        )
        self.assertEqual(response.json["data"]["status"], "complete")

        # can't update resolution
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
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
            '/monitors/{}/eliminationReport?acc_token={}'.format(self.monitor_id, self.tender_owner_token),
            {"data": {"description": "I want to change this description"}},
            status=422
        )


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorEliminationResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
