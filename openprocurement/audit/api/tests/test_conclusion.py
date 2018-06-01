from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
import unittest
from datetime import datetime


class MonitoringConclusionResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitoringConclusionResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))

    def test_fail_in_draft_status(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "description": "Sor lum far",
                    "violationOccurred": True,
                    "violationType": "corruptionProcurementMethodType",
                }
            }},
            status=422,
        )

    def test_decision_and_conclusion(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active",
                "decision": {
                    "description": "text",
                    "date": datetime.now().isoformat()
                },
                "conclusion": {
                    "description": "Some text",
                    "violationOccurred": True,
                    "violationType": "corruptionProcurementMethodType",
                }
            }}, status=422
        )


class ActiveMonitoringConclusionResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(ActiveMonitoringConclusionResourceTest, self).setUp()

        self.app.app.registry.docservice_url = 'http://localhost'

        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active",
                "decision": {
                    "description": "text",
                    "date": datetime.now().isoformat()
                }
            }}
        )

    def test_fail_empty(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {}
            }},
            status=422
        )
        self.assertEqual(
            ["This field is required."],
            response.json["errors"][0]["description"]["violationOccurred"],
        )

    def test_fail_valid_violation_flag(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": "Nope",
                }
            }},
            status=422
        )
        self.assertEqual(
            ["Must be either true or false."],
            response.json["errors"][0]["description"]["violationOccurred"],
        )

    def test_fail_required_type(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                }
            }},
            status=422
        )
        self.assertEqual(
            ["This field is required."],
            response.json["errors"][0]["description"]["violationType"],
        )

    def test_fail_valid_type(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": ["bloodTraitor"],
                }
            }},
            status=422
        )
        self.assertIn(
            "Value must be one of (",
            response.json["errors"][0]["description"]["violationType"][0][0],
        )

    def test_success_no_violations(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("conclusion", response.json["data"])
        self.assertEqual(response.json["data"]["conclusion"]["violationOccurred"], False)

    def test_success_minimal(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType"],
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("conclusion", response.json["data"])

        # add a document directly to a object
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "documents": [
                        {
                            'title': 'lorem.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    ],
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["data"]["conclusion"]["documents"]), 1)
        self.assertIn("id", response.json["data"]["conclusion"]["documents"][0])

        # post another document via the conclusion documents resource url
        response = self.app.post_json(
            '/monitorings/{}/conclusion/documents'.format(self.monitoring_id),
            {"data": {
                'title': 'sign.p7s',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/pkcs7-signature',
            }}
        )
        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            '/monitorings/{}/conclusion/documents'.format(self.monitoring_id))
        self.assertEqual(len(response.json["data"]), 2)

    def test_fail_violation_other(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType", "other"],
                }
            }},
            status=422
        )
        self.assertEqual(
            response.json['errors'],
            [{u'description': {u'otherViolationType': [u'This field is required.']},
              u'location': u'body', u'name': u'conclusion'}])

    def test_success_violation_other(self):
        data = {
            "conclusion": {
                "violationOccurred": True,
                "violationType": ["corruptionProcurementMethodType", "other"],
                "otherViolationType": "being too conciliatory",
            }
        }
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": data},
        )
        self.assertEqual(response.json['data']["conclusion"]["otherViolationType"],
                         data["conclusion"]["otherViolationType"])

        patch_data = {"conclusion": {"violationType": ["corruptionProcurementMethodType"]}}
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": patch_data},
        )
        self.assertNotIn("otherViolationType", response.json['data']["conclusion"])

    def test_success_full(self):
        conclusion = {
            "violationOccurred": True,
            "violationType": ["corruptionProcurementMethodType"],
            "auditFinding": "Ring around the rosies",
            "stringsAttached": "Pocket full of posies",
            "description": "Ashes, ashes, we all fall down",
            "documents": [
                {
                    'title': 'lorem.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                },
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
                "conclusion": conclusion
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("conclusion", response.json["data"])
        resp_conclusion = response.json["data"]["conclusion"]

        self.assertEqual(resp_conclusion["violationOccurred"], conclusion["violationOccurred"])
        self.assertEqual(resp_conclusion["violationType"], conclusion["violationType"])
        self.assertEqual(resp_conclusion["auditFinding"], conclusion["auditFinding"])
        self.assertEqual(resp_conclusion["stringsAttached"], conclusion["stringsAttached"])
        self.assertEqual(resp_conclusion["description"], conclusion["description"])
        self.assertEqual(len(resp_conclusion["documents"]), 2)

    def test_visibility(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "description": "text",
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType"],
                }
            }}
        )

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('conclusion', response.json['data'])

        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "addressed"
            }}
        )

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "text")


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitoringConclusionResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
