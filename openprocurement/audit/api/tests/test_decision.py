from freezegun import freeze_time
from openprocurement.api.constants import TZ
from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
import unittest
from datetime import datetime, timedelta


class MonitorDecisionResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitorDecisionResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitor()
        self.app.authorization = ('Basic', (self.sas_token, ''))

    def test_fail_empty(self):
        self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "decision": {}
            }},
            status=422
        )

    def test_success_minimal(self):
        decision_date = (datetime.now(TZ) - timedelta(days=2))
        response = self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": decision_date.isoformat()
                }
            }}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["id"], self.monitor_id)
        self.assertEqual(response.json['data']["status"], "draft")
        self.assertEqual(response.json['data']["decision"]["description"], "text")
        self.assertEqual(response.json['data']["decision"]["date"], decision_date.isoformat())

        # add a document directly to a object
        response = self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                "decision": {
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
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]["decision"]["documents"]), 1)
        self.assertIn("id", response.json["data"]["decision"]["documents"][0])

        # post another document via the decision documents resource url
        response = self.app.post_json(
            '/monitors/{}/decision/documents?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {
                'title': 'sign.p7s',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/pkcs7-signature',
            }}
        )
        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            '/monitors/{}/decision/documents?acc_token={}'.format(self.monitor_id, self.monitor_token))
        self.assertEqual(len(response.json["data"]), 2)

    def test_success_full(self):
        decision_date = (datetime.now(TZ) - timedelta(days=2))
        decision = {
            "description": "text",
            "date": decision_date.isoformat(),
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
                "decision": decision
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("decision", response.json["data"])
        self.assertEqual(response.json['data']["id"], self.monitor_id)
        self.assertEqual(response.json['data']["status"], "draft")
        self.assertEqual(response.json['data']["decision"]["description"], "text")
        self.assertEqual(response.json['data']["decision"]["date"], decision_date.isoformat())
        self.assertEqual(len(response.json['data']["decision"]["documents"]), 2)


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorDecisionResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
