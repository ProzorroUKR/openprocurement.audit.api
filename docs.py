from freezegun import freeze_time
from hashlib import sha512
from webtest import TestApp
from datetime import datetime
import openprocurement.audit.api.tests.base as base_test
import ConfigParser
import json
import mock
import uuid
import os


class DumpsTestAppwebtest(TestApp):
    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = "api-sandbox.openprocurement.org"
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                        '\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8'))
                    self.file_obj.write("\n")
                except:
                    pass
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('\n%s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write('\n' + json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8'))
                except:
                    pass
            self.file_obj.write("\n\n")
        return resp


@freeze_time("2018.01.01 00:00")
class BaseDocWebTest(base_test.BaseWebTest):

    def setUp(self):
        self.app = DumpsTestAppwebtest(
            "config:tests.ini", relative_to=os.path.dirname(base_test.__file__))
        self.app.RequestClass = base_test.PrefixedRequestClass
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db

        config = ConfigParser.RawConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'openprocurement/audit/api/tests/auth.ini'))
        self.sas_token = config.get("sas", "test_sas")
        self.broker_token = config.get("brokers", "broker")

        self.uuid_counter = 0
        self.uuid_patches = [
            mock.patch(path, side_effect=self._generate_test_uuid)
            for path in (
                'openprocurement.api.utils.uuid4',
                'openprocurement.audit.api.tests.base.uuid4',
                'openprocurement.api.models.uuid4',
                'openprocurement.audit.api.models.uuid4',
            )
        ]
        for p in self.uuid_patches:
            p.start()

    def tearDown(self):
        for p in self.uuid_patches:
            p.stop()
        super(BaseDocWebTest, self).tearDown()

    def _generate_test_uuid(self):
        self.uuid_counter += 1
        return uuid.uuid3(uuid.UUID(int=0), self.id() + str(self.uuid_counter))


class OptionsResourceTest(BaseDocWebTest):

    def test_monitoring_list_options_query_params(self):
        with open('docs/source/feed/http/monitorings-with-options.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', (self.sas_token, ''))
            response = self.app.post_json(
                '/monitorings',
                {
                    "options": {"pretty": True},
                    "data": {
                        "tender_id": self._generate_test_uuid().hex,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"]
                    }
                },
                status=201
            )
        self.assertEqual(response.status, '201 Created')

        with open('docs/source/feed/http/monitorings-with-options-query-params.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?opt_fields=status')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)


class MonitoringsResourceTest(BaseDocWebTest, base_test.DSWebTestMixin):
    def setUp(self):
        super(MonitoringsResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://docs-sandbox.openprocurement.org'

        self.party_creator = {
            "name": "The State Audit Service of Ukraine",
            "contactPoint": {
                "name": "Oleksii Kovalenko",
                "telephone": "0440000000"
            },
            "identifier": {
                "scheme": "UA-EDR",
                "id": "40165856",
                "uri": "http://www.dkrs.gov.ua"
            },
            "address": {
                "countryName": "Ukraine",
                "postalCode": "04070",
                "region": "Kyiv",
                "streetAddress": "Petra Sahaidachnoho St, 4",
                "locality": "Kyiv"
            },
            "roles": [
                "create"
            ]
        }

        self.party_decision = {
            "name": "The State Audit Service of Ukraine",
            "contactPoint": {
                "name": "John Doe",
                "telephone": "0440000000"
            },
            "identifier": {
                "scheme": "UA-EDR",
                "id": "40165856",
                "uri": "http://www.dkrs.gov.ua"
            },
            "address": {
                "countryName": "Ukraine",
                "postalCode": "04070",
                "region": "Kyiv",
                "streetAddress": "Petra Sahaidachnoho St, 4",
                "locality": "Kyiv"
            },
            "roles": [
                "decision"
            ]
        }

        self.party_dialogue = {
            "name": "The State Audit Service of Ukraine",
            "contactPoint": {
                "name": "Jane Doe",
                "telephone": "0440000000"
            },
            "identifier": {
                "scheme": "UA-EDR",
                "id": "40165856",
                "uri": "http://www.dkrs.gov.ua"
            },
            "address": {
                "countryName": "Ukraine",
                "postalCode": "04070",
                "region": "Kyiv",
                "streetAddress": "Petra Sahaidachnoho St, 4",
                "locality": "Kyiv"
            },
            "roles": [
                "dialogue"
            ]
        }

    @mock.patch('openprocurement.audit.api.validation.TendersClient')
    def test_monitoring_life_cycle_with_violations(self, mock_api_client):
        tender_token = self._generate_test_uuid().hex
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(tender_token).hexdigest()}
        }

        self.app.authorization = ('Basic', (self.sas_token, ''))

        with open('docs/source/tutorial/http/monitorings-empty.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings', status=200)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data'], [])

        with open('docs/source/tutorial/http/monitoring-post-empty-body.http', 'w') as self.app.file_obj:
            self.app.post_json('/monitorings', {"data": {}}, status=422)

        with open('docs/source/tutorial/http/monitoring-post.http', 'w') as self.app.file_obj:
            response = self.app.post_json(
                '/monitorings',
                {"data": {
                    "tender_id": self._generate_test_uuid().hex,
                    "reasons": ["public", "fiscal"],
                    "procuringStages": ["awarding", "contracting"],
                    "parties": [self.party_creator]
                }},
                status=201
            )

            monitoring_id = response.json["data"]["id"]

        with open('docs/source/tutorial/http/monitorings-with-object.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        with freeze_time("2018.01.02 00:00"):
            with open('docs/source/tutorial/http/monitoring-publish-wo-decision.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {"status": "active"}},
                    status=422
                )

        # PUBLISH
        with freeze_time("2018.01.02 01:00"):
            with open('docs/source/tutorial/http/monitoring-publish-party.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/parties'.format(monitoring_id),
                    {"data": self.party_decision},
                    status=201
                )

        with freeze_time("2018.01.02 01:05"):
            with open('docs/source/tutorial/http/monitoring-publish-first-step.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "decision": {
                            "description": "text",
                            "date": datetime.now().isoformat(),
                            "documents": [{
                                'title': 'lorem.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }]
                        }
                    }},
                    status=200
                )

        with freeze_time("2018.01.02 01:10"):
            with open('docs/source/tutorial/http/monitoring-publish-add-document.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/decision/documents'.format(monitoring_id),
                    {"data": {
                        'title': 'dolor.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }},
                    status=201
                )

        with freeze_time("2018.01.02 01:15"):
            with open('docs/source/tutorial/http/monitoring-publish-second-step.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "status": "active"
                    }},
                    status=200
                )

        with freeze_time("2018.01.02 01:20"):
            with open('docs/source/tutorial/http/monitoring-publish-change.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "decision": {
                            "description": "another_text",
                        }
                    }},
                    status=422
                )

        # DIALOGUE
        with freeze_time("2018.01.03 00:00"):
            with open('docs/source/tutorial/http/dialogue-party.http', 'w') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/parties'.format(monitoring_id),
                    {"data": self.party_dialogue},
                    status=201
                )

        party_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:05"):
            with open('docs/source/tutorial/http/dialogue-publish.http', 'w') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/dialogues'.format(monitoring_id),
                    {"data": {
                        "title": "Lorem ipsum",
                        "description": "Lorem ipsum dolor sit amet.",
                        "documents": [{
                            'title': 'ipsum.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }],
                        "relatedParty": party_id
                    }},
                    status=201
                )

        dialogue_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:10"):
            with open('docs/source/tutorial/http/dialogue-publish-add-document.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/dialogues/{}/documents'.format(monitoring_id, dialogue_id),
                    {"data": {
                        'title': 'dolor.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }},
                    status=201
                )

        with open('docs/source/tutorial/http/dialogue-get-documents.http', 'w') as self.app.file_obj:
            self.app.get(
                '/monitorings/{}/dialogues/{}/documents'.format(monitoring_id, dialogue_id),
                status=200
            )

        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.04 00:00"):
            with open('docs/source/tutorial/http/dialogue-get-credentials.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}/credentials?acc_token={}'.format(monitoring_id, tender_token),
                    status=200
                )

        tender_owner_token = response.json['access']['token']

        with freeze_time("2018.01.04 00:05"):
            with open('docs/source/tutorial/http/dialogue-answer.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}/dialogues/{}?acc_token={}'.format(monitoring_id, dialogue_id, tender_owner_token),
                    {"data": {
                        'answer': 'Sit amet'
                    }},
                    status=200
                )

        with freeze_time("2018.01.04 00:10"):
            with open('docs/source/tutorial/http/dialogue-answer-docs.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/dialogues/{}/documents?acc_token={}'.format(monitoring_id, dialogue_id, tender_owner_token),
                    {"data": {
                        'title': 'dolor.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }},
                    status=201
                )

        with open('docs/source/tutorial/http/dialogue-get.http', 'w') as self.app.file_obj:
            self.app.get(
                '/monitorings/{}/dialogues/{}'.format(monitoring_id, dialogue_id),
                status=200
            )

        self.app.authorization = ('Basic', (self.sas_token, ''))

        # CONCLUSION
        with freeze_time("2018.01.05 00:00"):
            with open('docs/source/tutorial/http/conclusion-wo-violations.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "conclusion": {
                            "violationOccurred": False,
                        }
                    }},
                )

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json["data"]["conclusion"]["violationOccurred"], False)

        with freeze_time("2018.01.05 00:10"):
            with open('docs/source/tutorial/http/conclusion-failed-required.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "conclusion": {
                            "violationOccurred": True,
                        }
                    }},
                    status=422
                )

        self.assertEqual(len(response.json["errors"]), 1)

        with freeze_time("2018.01.05 00:15"):
            with open('docs/source/tutorial/http/conclusion-full.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "conclusion": {
                            "violationOccurred": True,
                            "violationType": ["documentsForm", "corruptionAwarded"],
                            "auditFinding": "Ring around the rosies",
                            "stringsAttached": "Pocket full of posies",
                            "description": "Ashes, ashes, we all fall down",
                            "documents": [
                                {
                                    'title': 'New document(2).doc',
                                    'url': self.generate_docservice_url(),
                                    'hash': 'md5:' + '0' * 32,
                                    'format': 'application/msword',
                                }
                            ]
                        }
                    }}
                )
            self.assertEqual(response.status_code, 200)

        with freeze_time("2018.01.05 00:17"):
            with open('docs/source/tutorial/http/conclusion-other-validation.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "conclusion": {
                            "violationType": ["documentsForm", "corruptionAwarded", "other"],
                        }
                    }},
                    status=422
                )
                self.assertEqual(
                    response.json['errors'],
                    [{u'description': {u'otherViolationType': [u'This field is required.']},
                      u'location': u'body', u'name': u'conclusion'}])

        with freeze_time("2018.01.05 00:20"):
            with open('docs/source/tutorial/http/conclusion-add-document.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/conclusion/documents'.format(monitoring_id, dialogue_id),
                    {"data": {
                        'title': 'sign.p7s',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/pkcs7-signature',
                    }},
                    status=201
                )

        with freeze_time("2018.01.05 00:25"):
            with open('docs/source/tutorial/http/conclusion-addressed.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "status": "addressed",
                    }}
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["status"], "addressed")

        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.06 00:00"):
            with open('docs/source/tutorial/http/conclusion-dialogue.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/dialogues?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        "title": "Sit amet",
                        "description": "Sit amet lorem ipsum dolor.",
                        "documents": [{
                            'title': 'dolor.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }]
                    }},
                    status=201
                )

        # ELIMINATION REPORT
        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.07 00:00"):
            with open('docs/source/tutorial/http/elimination-report-post.http', 'w') as self.app.file_obj:
                response = self.app.put_json(
                    '/monitorings/{}/eliminationReport?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        "description": "The procurement requirements have been fixed and the changes are attached.",
                        "documents": [
                            {
                                'title': 'requirements.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }
                        ],
                    }},
                )

        self.assertEqual(response.status_code, 200)

        with freeze_time("2018.01.08 00:00"):
            with open('docs/source/tutorial/http/elimination-report-edit.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}/eliminationReport?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        "description": "The procurement requirements have been fixed and the changes are attached. "
                                       "But unfortunately the award cannot be changed as "
                                       "the procurement is in its final state.",
                    }},
                )

        self.assertEqual(response.status_code, 200)

        # ELIMINATION RESOLUTION
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.09 00:00"):
            with open('docs/source/tutorial/http/elimination-resolution-post.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "eliminationResolution": {
                            "result": "partly",
                            "resultByType": {
                                "documentsForm": "eliminated",
                                "corruptionAwarded": "not_eliminated",
                            },
                            "description": "The award hasn't been fixed.",
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

        with freeze_time("2018.01.25 00:00"):
            with open('docs/source/tutorial/http/monitoring-to-completed.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "status": "completed",
                    }},
                    status=200
                )

    def test_monitoring_life_cycle_with_no_violations(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/monitorings',
                {"data": {
                    "tender_id": self._generate_test_uuid().hex,
                    "reasons": ["public", "fiscal"],
                    "procuringStages": ["awarding", "contracting"],
                    "parties": [self.party_creator]
                }},
                status=201
            )

        monitoring_id = response.json["data"]["id"]

        with freeze_time("2018.01.02 00:00"):
            with open('docs/source/tutorial/http/monitoring-publish.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "status": "active",
                        "decision": {
                            "description": "text",
                            "date": datetime.now().isoformat(),
                            "documents": [{
                                'title': 'lorem.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }]
                        }
                    }},
                    status=200
                )

        with freeze_time("2018.01.03 00:00"):
            response = self.app.post_json(
                '/monitorings/{}/parties'.format(monitoring_id),
                {"data": self.party_dialogue},
                status=201
            )

        party_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:10"):
            self.app.post_json(
                '/monitorings/{}/dialogues'.format(monitoring_id),
                {"data": {
                    "title": "Lorem ipsum",
                    "description": "Lorem ipsum dolor sit amet.",
                    "documents": [{
                        'title': 'ipsum.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }],
                    "relatedParty": party_id
                }},
                status=201
            )

        with freeze_time("2018.01.04 00:00"):
            self.app.patch_json(
                '/monitorings/{}'.format(monitoring_id),
                {"data": {
                    "conclusion": {
                        "violationOccurred": False,
                    },
                    "status": "declined"
                }},
            )

        with freeze_time("2018.01.11 00:00"):
            with open('docs/source/tutorial/http/monitoring-to-closed.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "status": "closed",
                    }}
                )

    def test_monitoring_life_cycle_stopped(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/monitorings',
                {"data": {
                    "tender_id": self._generate_test_uuid().hex,
                    "reasons": ["public", "fiscal"],
                    "procuringStages": ["awarding", "contracting"],
                    "parties": [self.party_creator]
                }},
                status=201
            )

        monitoring_id = response.json["data"]["id"]

        with freeze_time("2018.01.02 00:00"):
            self.app.patch_json(
                '/monitorings/{}'.format(monitoring_id),
                {"data": {
                    "status": "active",
                    "decision": {
                        "description": "text",
                        "date": datetime.now().isoformat(),
                        "documents": [{
                            'title': 'lorem.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }]
                    }
                }},
                status=200
            )

        with freeze_time("2018.01.03 00:00"):
            with open('docs/source/tutorial/http/monitoring-to-stopped.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "cancellation": {
                            "description": "Complaint was created"
                        },
                        "status": "stopped",
                    }}
                )

    def test_monitoring_life_cycle_cancelled(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/monitorings',
                {"data": {
                    "tender_id": self._generate_test_uuid().hex,
                    "reasons": ["public", "fiscal"],
                    "procuringStages": ["awarding", "contracting"],
                    "parties": [self.party_creator]
                }},
                status=201
            )

        monitoring_id = response.json["data"]["id"]

        with freeze_time("2018.01.03 00:00"):
            with open('docs/source/tutorial/http/monitoring-to-cancelled.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "cancellation": {
                            "description": "Some reason"
                        },
                        "status": "cancelled",
                    }}
                )


class FeedDocsTest(BaseDocWebTest):

    def setUp(self):
        super(FeedDocsTest, self).setUp()

        for i in range(5):
            self.create_monitoring()

    def test_changes_feed(self):
        with open('docs/source/feed/http/changes-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&limit=3&opt_fields=reasons')

            self.assertEqual(len(response.json["data"]), 3)
            self.assertIn("next_page", response.json)

        with open('docs/source/feed/http/changes-feed-next.http', 'w') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 2)
            self.assertIn("next_page", response.json)

        with open('docs/source/feed/http/changes-feed-last.http', 'w') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 0)
            self.assertIn("next_page", response.json)

        self.create_monitoring()

        with open('docs/source/feed/http/changes-feed-new.http', 'w') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)

        next_url = response.json["next_page"]["path"]

        with open('docs/source/feed/http/changes-feed-new-next.http', 'w') as self.app.file_obj:
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 0)
            self.assertIn("next_page", response.json)

        self.create_monitoring()

        # TODO: why doesn't this make the tender be shown on the next page?
        # self.app.authorization = ('Basic', (self.sas_token, ''))
        # self.app.patch_json(
        #     '/monitorings/{}?acc_token={}'.format(self.monitoring_id, monitoring_token),
        #     {'data': {"reasons": ['media', 'public']}}
        # )

        with open('docs/source/feed/http/changes-feed-new-last.http', 'w') as self.app.file_obj:
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)
