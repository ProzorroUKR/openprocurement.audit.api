import unittest

from datetime import datetime

from openprocurement.audit.api.constants import ADDRESSED_STATUS, ACTIVE_STATUS
from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


class MonitoringConclusionResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitoringConclusionResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

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
                "status": ACTIVE_STATUS,
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

        self.create_monitoring(parties=[self.initial_party])
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": ACTIVE_STATUS,
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
        doc_hash = '2' * 32
        response = self.app.post_json(
            '/monitorings/{}/conclusion/documents'.format(self.monitoring_id),
            {"data": {
                'title': 'sign.p7s',
                'url': self.generate_docservice_url(doc_hash=doc_hash),
                'hash': 'md5:' + doc_hash,
                'format': 'application/pkcs7-signature',
            }}
        )
        self.assertEqual(response.status_code, 201)
        doc_data = response.json["data"]

        response = self.app.get(
            '/monitorings/{}/conclusion/documents'.format(self.monitoring_id))
        self.assertEqual(len(response.json["data"]), 2)

        # update  document
        request_data = {
            'title': 'sign-1.p7s',
            'url': self.generate_docservice_url(),
            'format': 'application/json',
            'hash': 'md5:' + '0' * 32,
        }
        response = self.app.put_json(
            '/monitorings/{}/conclusion/documents/{}'.format(
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
            '/monitorings/{}/conclusion/documents/{}'.format(
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

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('conclusion', response.json['data'])

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": ADDRESSED_STATUS
            }}
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "text")

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "text")

    def test_conclusion_endpoint(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.get('/monitorings/{}/conclusion'.format(self.monitoring_id), status=403)

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
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.get('/monitorings/{}/conclusion'.format(self.monitoring_id), status=403)
        self.app.authorization = None
        self.app.get('/monitorings/{}/conclusion'.format(self.monitoring_id), status=403)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/monitorings/{}/conclusion'.format(self.monitoring_id))
        self.assertEqual(set(response.json["data"].keys()),
                         {"dateCreated", "description", "violationOccurred", "violationType"})

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": ADDRESSED_STATUS
            }}
        )

        self.app.authorization = None
        response = self.app.get('/monitorings/{}/conclusion'.format(self.monitoring_id))
        self.assertEqual(set(response.json["data"].keys()),
                         {"dateCreated", "description", "datePublished", "violationOccurred", "violationType"})

    def test_conclusion_party_create(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        party_id = response.json['data']['parties'][0]['id']

        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                    "relatedParty": party_id
                }
            }}
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['conclusion']['relatedParty'], party_id)

    def test_conclusion_party_create_party_id_not_exists(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                    "relatedParty": "Party with the devil"
                }
            }}, status=422
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual(
            ('body', 'conclusion', 'relatedParty'),
            next(get_errors_field_names(response, 'relatedParty should be one of parties.')))

    def test_restricted_visibility(self):
        self.create_monitoring(parties=[self.initial_party], restricted_config=True)
        self.app.patch_json(
            f'/monitorings/{self.monitoring_id}',
            {"data": {
                "status": ACTIVE_STATUS,
                "decision": {
                    "description": "text",
                    "date": datetime.now().isoformat()
                }
            }}
        )
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
        self.app.patch_json(
            f'/monitorings/{self.monitoring_id}',
            {"data": {
                "conclusion": conclusion,
                "status": ADDRESSED_STATUS,
            }}
        )

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "Ashes, ashes, we all fall down")
        self.assertEqual(response.json['data']["conclusion"]["auditFinding"], "Ring around the rosies")
        self.assertEqual(response.json['data']["conclusion"]["stringsAttached"], "Pocket full of posies")
        self.assertEqual(response.json['data']["conclusion"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["conclusion"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "Ashes, ashes, we all fall down")
        self.assertEqual(response.json['data']["conclusion"]["auditFinding"], "Ring around the rosies")
        self.assertEqual(response.json['data']["conclusion"]["stringsAttached"], "Pocket full of posies")
        self.assertEqual(response.json['data']["conclusion"]["documents"][0]["title"], "lorem.doc")
        self.assertIn("http://localhost", response.json['data']["conclusion"]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/monitorings/{self.monitoring_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["description"], "Приховано")
        self.assertEqual(response.json['data']["conclusion"]["description"], "Приховано")
        self.assertEqual(response.json['data']["conclusion"]["auditFinding"], "Приховано")
        self.assertEqual(response.json['data']["conclusion"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["conclusion"]["documents"][0]["url"], "Приховано")
