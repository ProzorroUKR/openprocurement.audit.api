import unittest

from datetime import datetime, timedelta

from openprocurement.audit.api.constants import ACTIVE_STATUS, TZ
from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


class MonitoringDecisionResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringDecisionResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'
        self.create_monitoring(parties=[self.initial_party])
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

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
        doc_hash = '2' * 32
        response = self.app.post_json(
            '/monitorings/{}/decision/documents'.format(self.monitoring_id),
            {"data": {
                'title': 'sign.p7s',
                'url': self.generate_docservice_url(doc_hash=doc_hash),
                'hash': 'md5:' + doc_hash,
                'format': 'application/pkcs7-signature',
            }}
        )
        self.assertEqual(response.status_code, 201)
        doc_data = response.json["data"]

        response = self.app.get('/monitorings/{}/decision/documents'.format(self.monitoring_id))
        self.assertEqual(len(response.json["data"]), 2)

        # update  document
        request_data = {
            'title': 'sign-1.p7s',
            'url': self.generate_docservice_url(),
            'format': 'application/json',
            'hash': 'md5:' + '0' * 32,
        }
        response = self.app.put_json(
            '/monitorings/{}/decision/documents/{}'.format(
                self.monitoring_id,
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
            'hash': 'md5:' + '1' * 32,
        }
        response = self.app.patch_json(
            '/monitorings/{}/decision/documents/{}'.format(
                self.monitoring_id,
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

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('decision', response.json['data'])

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": ACTIVE_STATUS
            }}
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")

    def test_decision_endpoint(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.get('/monitorings/{}/decision'.format(self.monitoring_id), status=403)

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": datetime.now(TZ).isoformat(),
                    "documents": [
                        {
                            'title': 'lorem.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    ]
                }
            }}
        )
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.get('/monitorings/{}/decision'.format(self.monitoring_id), status=403)
        self.app.authorization = None
        self.app.get('/monitorings/{}/decision'.format(self.monitoring_id), status=403)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}/decision'.format(self.monitoring_id))
        self.assertEqual(set(response.json["data"].keys()),
                         {"date", "dateCreated", "description", "documents"})

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": ACTIVE_STATUS
            }}
        )

        self.app.authorization = None
        response = self.app.get('/monitorings/{}/decision'.format(self.monitoring_id))
        self.assertEqual(set(response.json["data"].keys()),
                         {"date", "dateCreated", "description", "documents", "datePublished"})

    def test_decision_party_create(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        party_id = response.json['data']['parties'][0]['id']

        decision_date = (datetime.now(TZ) - timedelta(days=2))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": decision_date.isoformat(),
                    "relatedParty": party_id
                }
            }}
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['decision']['relatedParty'], party_id)

    def test_dialogue_party_create_party_id_not_exists(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        decision_date = (datetime.now(TZ) - timedelta(days=2))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text",
                    "date": decision_date.isoformat(),
                    "relatedParty": "Party with the devil"
                }
            }}, status=422
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'decision', 'relatedParty'),
            next(get_errors_field_names(response, 'relatedParty should be one of parties.')))

    def test_restricted_visibility(self):
        self.create_monitoring(parties=[self.initial_party], restricted_config=True)
        self.app.patch_json(
            f'/monitorings/{self.monitoring_id}',
            {"data": {
                "status": ACTIVE_STATUS,
                "decision": {
                    "description": "text",
                    "date": datetime.now(TZ).isoformat(),
                    "documents": [
                        {
                            'title': 'lorem.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    ]
                }
            }}
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")
        self.assertEqual(response.json['data']["decision"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["decision"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "text")
        self.assertEqual(response.json['data']["decision"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["decision"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"]["description"], "Приховано")
        self.assertEqual(response.json['data']["decision"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["decision"]["documents"][0]["url"], "Приховано")
