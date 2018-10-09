from freezegun import freeze_time
from hashlib import sha512
from webtest import TestApp, AppError
from datetime import datetime
import openprocurement.audit.api.tests.base as base_test
import ConfigParser
import json
import mock
import uuid
import os


class DumpsTestAppwebtest(TestApp):
    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = "audit-api-sandbox.prozorro.gov.ua"
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
                    self.file_obj.write(
                        '\n' + json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8')
                    )
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
        return uuid.uuid3(uuid.UUID(int=0), self.id() + str(datetime.now()) + str(self.uuid_counter))

    def create_monitoring(self, **kwargs):
        try:
            return super(BaseDocWebTest, self).create_monitoring(**kwargs)
        except AppError:
            self.uuid_counter += 1
            self.create_monitoring(**kwargs)

    def create_active_monitoring(self, **kwargs):
        try:
            return super(BaseDocWebTest, self).create_active_monitoring(**kwargs)
        except AppError:
            self.uuid_counter += 1
            self.create_active_monitoring(**kwargs)


@freeze_time("2018.01.01 00:00")
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
            response = self.app.get('/monitorings?mode=real_draft&opt_fields=status')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)


@freeze_time("2018.01.01 00:00")
class MonitoringsResourceTest(BaseDocWebTest, base_test.DSWebTestMixin):
    def setUp(self):
        super(MonitoringsResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://docs-sandbox.openprocurement.org'

        self.party = {
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
                "sas"
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
                    "parties": [self.party]
                }},
                status=201
            )

            monitoring_id = response.json["data"]["id"]
            party_id = response.json["data"]["parties"][0]["id"]

        with open('docs/source/tutorial/http/monitorings-with-object.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=real_draft')
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
                            }],
                            "relatedParty": party_id
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

        # CREDENTIALS

        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.04 00:00"):
            with open('docs/source/tutorial/http/dialogue-get-credentials.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}/credentials?acc_token={}'.format(monitoring_id, tender_token),
                    status=200
                )

        tender_owner_token = response.json['access']['token']

        # DIALOGUE
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.03 00:05"):
            with open('docs/source/tutorial/http/post-publish.http', 'w') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts'.format(monitoring_id),
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

        post_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:10"):
            with open('docs/source/tutorial/http/post-publish-add-document.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts/{}/documents'.format(monitoring_id, post_id),
                    {"data": {
                        'title': 'dolor.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }},
                    status=201
                )

        with open('docs/source/tutorial/http/post-get-documents.http', 'w') as self.app.file_obj:
            self.app.get(
                '/monitorings/{}/posts/{}/documents'.format(monitoring_id, post_id),
                status=200
            )

        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.04 00:05"):
            with open('docs/source/tutorial/http/post-answer.http', 'w') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        'title': 'Sit amet',
                        'description': 'Dolor sit amet',
                        'relatedPost': post_id
                    }},
                    status=201
                )

        answer_id = response.json['data']['id']

        with freeze_time("2018.01.04 00:10"):
            with open('docs/source/tutorial/http/post-answer-docs.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts/{}/documents?acc_token={}'.format(
                        monitoring_id, answer_id, tender_owner_token
                    ),
                    {"data": {
                        'title': 'dolor.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }},
                    status=201
                )

        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.04 01:05"):
            with open('docs/source/tutorial/http/post-broker-publish.http', 'w') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        "title": "Dolor sit amet",
                        "description": "Lorem ipsum dolor sit amet.",
                        "documents": [{
                            'title': 'ipsum.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }]
                    }},
                    status=201
                )

        post_broker_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.04 01:15"):
            with open('docs/source/tutorial/http/post-broker-sas-answer.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts'.format(monitoring_id),
                    {"data": {
                        "title": "Lorem ipsum",
                        "description": "Lorem ipsum dolor sit amet.",
                        "relatedPost": post_broker_id,
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

        with open('docs/source/tutorial/http/posts-get.http', 'w') as self.app.file_obj:
            self.app.get(
                '/monitorings/{}/posts'.format(monitoring_id),
                status=200
            )

        # CONCLUSION
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with freeze_time("2018.01.05 00:00"):
            with open('docs/source/tutorial/http/conclusion-wo-violations.http', 'w') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "conclusion": {
                            "violationOccurred": False,
                            "relatedParty": party_id
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
                    '/monitorings/{}/conclusion/documents'.format(monitoring_id),
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
            with open('docs/source/tutorial/http/conclusion-post.http', 'w') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts?acc_token={}'.format(monitoring_id, tender_owner_token),
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

        post_conclusion_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:10"):
            with open('docs/source/tutorial/http/post-conclusion-add-document.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts/{}/documents?acc_token={}'.format(
                        monitoring_id, post_conclusion_id, tender_owner_token),
                    {"data": {
                        'title': 'dolor.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    }},
                    status=201
                )

        # APPEAL
        self.app.authorization = ('Basic', (self.broker_token, ''))

        with freeze_time("2018.01.06 07:00"):
            with open('docs/source/tutorial/http/appeal-post.http', 'w') as self.app.file_obj:
                response = self.app.put_json(
                    '/monitorings/{}/appeal?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        "description": "Appeal description",
                        "documents": [{
                            'title': 'letter.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }]
                    }},
                )
                appeal_doc_id = response.json["data"]["documents"][0]["id"]

        another_document = {
            'title': 'another-letter.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }

        with freeze_time("2018.01.06 07:30"):
            with open('docs/source/tutorial/http/appeal-post-again.http', 'w') as self.app.file_obj:
                self.app.put_json(
                    '/monitorings/{}/appeal?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": {
                        "description": "Addition to the appeal description",
                        "documents": [another_document]
                    }},
                    status=403
                )

        with freeze_time("2018.01.06 08:00"):
            with open('docs/source/tutorial/http/appeal-post-doc.http', 'w') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/appeal/documents?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": another_document},
                )

        with freeze_time("2018.01.06 08:15"):
            with open('docs/source/tutorial/http/appeal-patch-doc.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}/appeal/documents/{}?acc_token={}'.format(
                        monitoring_id,
                        appeal_doc_id,
                        tender_owner_token
                    ),
                    {"data": {
                        'title': 'letter(0).doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/json',
                    }},
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
                            ],
                            "relatedParty": party_id
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
                    "parties": [self.party]
                }},
                status=201
            )

        monitoring_id = response.json["data"]["id"]
        party_id = response.json["data"]["parties"][0]["id"]

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
                            }],
                            "relatedParty": party_id
                        }
                    }},
                    status=200
                )

        with freeze_time("2018.01.03 00:10"):
            self.app.post_json(
                '/monitorings/{}/posts'.format(monitoring_id),
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
                        "relatedParty": party_id
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
                    "parties": [self.party]
                }},
                status=201
            )

        monitoring_id = response.json["data"]["id"]
        party_id = response.json["data"]["parties"][0]["id"]

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
                        }],
                        "relatedParty": party_id
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
                            "description": "Complaint was created",
                            "relatedParty": party_id
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
                    "parties": [self.party]
                }},
                status=201
            )

        monitoring_id = response.json["data"]["id"]
        party_id = response.json["data"]["parties"][0]["id"]

        with freeze_time("2018.01.03 00:00"):
            with open('docs/source/tutorial/http/monitoring-to-cancelled.http', 'w') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {
                        "cancellation": {
                            "description": "Some reason",
                            "relatedParty": party_id
                        },
                        "status": "cancelled",
                    }}
                )


@freeze_time("2018.01.01 00:00")
class FeedDocsTest(BaseDocWebTest):

    def setUp(self):
        super(FeedDocsTest, self).setUp()

        for i in range(5):
            self.create_active_monitoring()

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

        self.create_active_monitoring()

        with open('docs/source/feed/http/changes-feed-new.http', 'w') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)

        next_url = response.json["next_page"]["path"]

        with open('docs/source/feed/http/changes-feed-new-next.http', 'w') as self.app.file_obj:
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 0)
            self.assertIn("next_page", response.json)

        self.create_active_monitoring()

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

@freeze_time("2018.01.01 00:00")
class PrivateFeedDocsTest(BaseDocWebTest):

    def create_items(self, **kwargs):
        self.tender_id = '13c14e6a15b24e1a982310f262e18e7a'
        kwargs.update(tender_id=self.tender_id)

        self.create_monitoring(**kwargs)  # draft

        self.create_monitoring(**kwargs)  # cancelled
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "cancellation": {
                    "description": "Some reason",
                },
                "status": "cancelled",
            }}
        )

        self.create_active_monitoring(**kwargs)  # active

    def test_feed_public(self):
        self.create_items()

        with open('docs/source/feed/http/public-changes-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&opt_fields=status')

            self.assertEqual(len(response.json["data"]), 1)

        with open('docs/source/feed/http/public-date-modified-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?opt_fields=status')

            self.assertEqual(len(response.json["data"]), 1)


        with open('docs/source/feed/http/public-tender-monitorings.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/monitorings'.format(self.tender_id))

            self.assertEqual(len(response.json["data"]), 1)

    def test_feed_public_test(self):
        self.create_items(mode="test")

        with open('docs/source/feed/http/public-test-changes-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=test&feed=changes&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 1)

        with open('docs/source/feed/http/public-test-date-modified-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=test&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 1)


        with open('docs/source/feed/http/public-test-tender-monitorings.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/monitorings?mode=test&opt_fields=mode'.format(self.tender_id))

            self.assertEqual(len(response.json["data"]), 1)

    def test_feed_private(self):
        self.create_items()

        with open('docs/source/feed/http/private-changes-feed-forbidden.http', 'w') as self.app.file_obj:
            self.app.get('/monitorings?feed=changes&mode=real_draft&opt_fields=status', status=403)

        self.app.authorization = ('Basic', (self.sas_token, ''))

        with open('docs/source/feed/http/private-changes-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&mode=real_draft&opt_fields=status')

            self.assertEqual(len(response.json["data"]), 3)

        with open('docs/source/feed/http/private-date-modified-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=real_draft&opt_fields=status')

            self.assertEqual(len(response.json["data"]), 3)


        with open('docs/source/feed/http/private-tender-monitorings.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/monitorings?mode=draft'.format(self.tender_id))

            self.assertEqual(len(response.json["data"]), 3)


    def test_feed_private_test(self):
        self.create_items(mode="test")

        self.app.authorization = ('Basic', (self.sas_token, ''))

        with open('docs/source/feed/http/private-test-changes-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&mode=all_draft&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 3)

        with open('docs/source/feed/http/private-test-date-modified-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=all_draft&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 3)
