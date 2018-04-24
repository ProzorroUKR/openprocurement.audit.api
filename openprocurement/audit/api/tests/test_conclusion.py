from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
import unittest
from datetime import datetime


class MonitorConclusionResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitorConclusionResourceTest, self).setUp()
        self.create_monitor()
        self.app.authorization = ('Basic', (self.sas_token, ''))

    def test_fail_in_draft_status(self):
        self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "conclusion": {
                    "description": "Sor lum far",
                    "violationOccurred": True,
                    "violationType": "corruptionProcurementMethodType",
                }
            }},
            status=403,
        )

    def test_decision_and_conclusion(self):
        self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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
            }}, status=403
        )


class ActiveMonitorConclusionResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(ActiveMonitorConclusionResourceTest, self).setUp()

        self.app.app.registry.docservice_url = 'http://localhost'

        self.create_monitor()
        self.app.authorization = ('Basic', (self.sas_token, ''))

        self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": "bloodyViolator",
                }
            }},
            status=422
        )
        self.assertIn(
            "Value must be one of (",
            response.json["errors"][0]["description"]["violationType"][0],
        )

    def test_success_no_violations(self):
        response = self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("conclusion", response.json["data"])
        self.assertEqual(response.json["data"]["conclusion"], {'violationOccurred': False})

    def test_success_minimal(self):
        response = self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": "corruptionProcurementMethodType",
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("conclusion", response.json["data"])

        # add a document directly to a object
        response = self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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
            '/monitors/{}/conclusion/documents?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                'title': 'sign.p7s',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/pkcs7-signature',
            }}
        )
        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            '/monitors/{}/conclusion/documents?acc_token={}'.format(self.monitor_id, self.monitor_token))
        self.assertEqual(len(response.json["data"]), 2)

    def test_success_full(self):
        conclusion = {
            "violationOccurred": True,
            "violationType": "corruptionProcurementMethodType",
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
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
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


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorConclusionResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
