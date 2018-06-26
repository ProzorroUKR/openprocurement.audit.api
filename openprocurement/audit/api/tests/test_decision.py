from freezegun import freeze_time
from openprocurement.api.constants import TZ
from openprocurement.audit.api.tests.base import BaseWebTest, DSWebTestMixin
import unittest
from datetime import datetime, timedelta


class MonitoringDecisionResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringDecisionResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))

    def test_fail_empty(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {}
            }},
            status=422
        )

    def test_success_minimal(self):
        decision_date = (datetime.now(TZ) - timedelta(days=2))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": decision_date.isoformat()
                }
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["id"], self.monitoring_id)
        self.assertEqual(response.json['data']["status"], "draft")
        self.assertEqual(response.json['data']["decision"]["description"], "text")
        self.assertEqual(response.json['data']["decision"]["date"], decision_date.isoformat())

        # add a document directly to a object
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["data"]["decision"]["documents"]), 1)
        self.assertIn("id", response.json["data"]["decision"]["documents"][0])

        # post another document via the decision documents resource url
        response = self.app.post_json(
            '/monitorings/{}/decision/documents'.format(self.monitoring_id),
            {"data": {
                'title': 'sign.p7s',
                'url': self.generate_docservice_url(),
                'hash': 'md5:' + '0' * 32,
                'format': 'application/pkcs7-signature',
            }}
        )
        self.assertEqual(response.status_code, 201)

        response = self.app.get('/monitorings/{}/decision/documents'.format(self.monitoring_id))
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
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": decision
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("decision", response.json["data"])
        self.assertEqual(response.json['data']["id"], self.monitoring_id)
        self.assertEqual(response.json['data']["status"], "draft")
        response_decision = response.json['data']["decision"]
        self.assertEqual(response_decision["description"], "text")
        self.assertEqual(response_decision["date"], decision_date.isoformat())
        self.assertEqual(len(response_decision["documents"]), 2)

        self.assertEqual(decision['documents'][0]['title'], response_decision['documents'][0]['title'])
        self.assertNotEqual(decision['documents'][0]['url'], response_decision['documents'][0]['url'])
        self.assertEqual(decision['documents'][1]['title'], response_decision['documents'][1]['title'])
        self.assertNotEqual(decision['documents'][1]['url'], response_decision['documents'][1]['url'])

    def test_visibility(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": datetime.now(TZ).isoformat()
                }
            }}
        )

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('decision', response.json['data'])

        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active"
            }}
        )

        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_token, ''))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitoringDecisionResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
