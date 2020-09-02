import json
import traceback
from hashlib import sha512, md5

from unittest import mock
import uuid
from datetime import datetime
from freezegun import freeze_time

from openprocurement.audit.api.choices import VIOLATION_TYPE_CHOICES
from openprocurement.audit.monitoring.tests.base import BaseWebTest as MonitoringWebTest, DSWebTestMixin
from openprocurement.audit.inspection.tests.base import BaseWebTest as InspectionWebTest
from openprocurement.audit.request.tests.base import BaseWebTest as RequestWebTest
from openprocurement.audit.api.tests.base import BaseTestApp

API_HOST = "audit-api-sandbox.prozorro.gov.ua"


class DumpsWebTestApp(BaseTestApp):
    hostname = API_HOST
    indent = 2
    ensure_ascii = False

    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = self.hostname
        self.write_request(req)
        resp = super(DumpsWebTestApp, self).do_request(req, status=status, expect_errors=expect_errors)
        self.write_response(resp)
        return resp

    def write_request(self, req):
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True).decode("utf-8"))
            self.file_obj.write("\n")
            if req.body:
                try:
                    obj = json.loads(req.body)
                except ValueError:
                    self.file_obj.write('DATA:\n' + req.body)
                else:
                    self.file_obj.write('DATA:\n' + json.dumps(
                        obj, indent=self.indent, ensure_ascii=self.ensure_ascii
                    ))
                self.file_obj.write("\n")
            self.file_obj.write("\n")

    def write_response(self, resp):
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [
                (n.title(), v)
                for n, v in resp.headerlist
                if n.lower() != 'content-length'
            ]
            headers.sort()
            self.file_obj.write(str('Response: %s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))
            if resp.testbody:
                try:
                    obj = json.loads(resp.testbody)
                except ValueError:
                    pass
                else:
                    self.file_obj.write(json.dumps(
                        obj, indent=self.indent, ensure_ascii=self.ensure_ascii
                    ))
                    self.file_obj.write("\n")
            self.file_obj.write("\n")


MOCK_DATETIME = '2019-04-01T00:00:00+02:00'


class MockWebTestMixin(object):
    uuid_patch = None
    uuid_counters = None
    tick_delta = None

    whitelist = ('/openprocurement/', '/docs.py')
    blacklist = ()

    def setUpMock(self):
        self.uuid_patch = mock.patch('uuid.UUID', side_effect=self.uuid)
        self.uuid_patch.start()

    def tearDownMock(self):
        self.uuid_patch.stop()

    def uuid(self, version=None, **kwargs):
        stack = self.stack()
        hex = md5(str(stack).encode("utf-8")).hexdigest()
        count = self.count(hex)
        hash = md5((hex + str(count)).encode("utf-8")).digest()
        self.uuid_patch.stop()
        test_uuid = uuid.UUID(bytes=hash[:16], version=version)
        self.uuid_patch.start()
        return test_uuid

    def stack(self):
        def trim_path(path):
            for whitelist_item in self.whitelist:
                pos = path.find(whitelist_item)
                if pos > -1:
                    return path[pos:]

        stack = traceback.extract_stack()
        return [(trim_path(item[0]), item[2], item[3]) for item in stack if all([
            any([path in item[0] for path in self.whitelist]),
            all([path not in item[0] for path in self.blacklist])
        ])]

    def count(self, name):
        if self.uuid_counters is None:
            self.uuid_counters = dict()
        if name not in self.uuid_counters:
            self.uuid_counters[name] = 0
        self.uuid_counters[name] += 1
        return self.uuid_counters[name]


class BaseMonitoringWebTest(MonitoringWebTest, MockWebTestMixin):
    AppClass = DumpsWebTestApp

    def setUp(self):
        self.setUpMock()
        super(BaseMonitoringWebTest, self).setUp()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

    def tearDown(self):
        super(BaseMonitoringWebTest, self).tearDown()
        self.tearDownMock()


class BaseInspectionWebTest(InspectionWebTest, MockWebTestMixin):
    AppClass = DumpsWebTestApp

    def setUp(self):
        self.setUpMock()
        super(BaseInspectionWebTest, self).setUp()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

    def tearDown(self):
        super(BaseInspectionWebTest, self).tearDown()
        self.tearDownMock()


class BaseRequestWebTest(RequestWebTest, MockWebTestMixin):
    AppClass = DumpsWebTestApp

    def setUp(self):
        self.setUpMock()
        super(BaseRequestWebTest, self).setUp()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

    def tearDown(self):
        super(BaseRequestWebTest, self).tearDown()
        self.tearDownMock()


@freeze_time("2018.01.01 00:00")
class OptionsResourceTest(BaseMonitoringWebTest):

    def test_monitoring_list_options_query_params(self):
        with open('docs/source/monitoring/feed/http/monitorings-with-options.http', 'wt') as self.app.file_obj:
            self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
            response = self.app.post_json(
                '/monitorings',
                {
                    "options": {"pretty": True},
                    "data": {
                        "tender_id": self.uuid().hex,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"]
                    }
                },
                status=201
            )
        self.assertEqual(response.status, '201 Created')

        with open('docs/source/monitoring/feed/http/monitorings-with-options-query-params.http',
                  'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=real_draft&opt_fields=status')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)


@freeze_time("2018.01.01 00:00")
class MonitoringsResourceTest(BaseMonitoringWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringsResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://public-docs-sandbox.prozorro.gov.ua'

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

    @mock.patch('openprocurement.audit.monitoring.validation.TendersClient')
    def test_monitoring_life_cycle_with_violations(self, mock_api_client):
        tender_token = self.uuid().hex
        mock_api_client.return_value.extract_credentials.return_value = {
            'data': {'tender_token': sha512(tender_token.encode()).hexdigest()}
        }

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with open('docs/source/monitoring/tutorial/http/monitorings-empty.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings', status=200)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data'], [])

        with open('docs/source/monitoring/tutorial/http/monitoring-post-empty-body.http', 'wt') as self.app.file_obj:
            self.app.post_json('/monitorings', {"data": {}}, status=422)

        with open('docs/source/monitoring/tutorial/http/monitoring-post.http', 'wt') as self.app.file_obj:
            response = self.app.post_json(
                '/monitorings',
                {
                    "data": {
                        "tender_id": self.uuid().hex,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"],
                        "parties": [self.party]
                    }
                },
                status=201
            )

            monitoring_id = response.json["data"]["id"]
            party_id = response.json["data"]["parties"][0]["id"]

        with open('docs/source/monitoring/tutorial/http/monitorings-with-object.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=real_draft')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        with freeze_time("2018.01.02 00:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-publish-wo-decision.http',
                      'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {"data": {"status": "active"}},
                    status=422
                )

        # PUBLISH

        with freeze_time("2018.01.02 01:05"):
            with open('docs/source/monitoring/tutorial/http/monitoring-publish-first-step.http',
                      'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
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
                        }
                    },
                    status=200
                )

        with freeze_time("2018.01.02 01:10"):
            with open('docs/source/monitoring/tutorial/http/monitoring-publish-add-document.http',
                      'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/decision/documents'.format(monitoring_id),
                    {
                        "data": {
                            'title': 'dolor.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    },
                    status=201
                )

        with freeze_time("2018.01.02 01:15"):
            with open('docs/source/monitoring/tutorial/http/monitoring-publish-second-step.http',
                      'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "status": "active"
                        }
                    },
                    status=200
                )

        with freeze_time("2018.01.02 01:20"):
            with open('docs/source/monitoring/tutorial/http/monitoring-publish-change.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "decision": {
                                "description": "another_text",
                            }
                        }
                    },
                    status=422
                )

        # CREDENTIALS

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        with freeze_time("2018.01.04 00:00"):
            with open('docs/source/monitoring/tutorial/http/dialogue-get-credentials.http', 'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}/credentials?acc_token={}'.format(monitoring_id, tender_token),
                    status=200
                )

        tender_owner_token = response.json['access']['token']

        # DIALOGUE
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.03 00:05"):
            with open('docs/source/monitoring/tutorial/http/post-publish.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts'.format(monitoring_id),
                    {
                        "data": {
                            "title": "Lorem ipsum",
                            "description": "Lorem ipsum dolor sit amet.",
                            "documents": [{
                                'title': 'ipsum.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }],
                            "relatedParty": party_id
                        }
                    },
                    status=201
                )

        post_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:10"):
            with open('docs/source/monitoring/tutorial/http/post-publish-add-document.http', 'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts/{}/documents'.format(monitoring_id, post_id),
                    {
                        "data": {
                            'title': 'dolor.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    },
                    status=201
                )

        with open('docs/source/monitoring/tutorial/http/post-get-documents.http', 'wt') as self.app.file_obj:
            self.app.get(
                '/monitorings/{}/posts/{}/documents'.format(monitoring_id, post_id),
                status=200
            )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        with freeze_time("2018.01.04 00:05"):
            with open('docs/source/monitoring/tutorial/http/post-answer.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {
                        "data": {
                            'title': 'Sit amet',
                            'description': 'Dolor sit amet',
                            'relatedPost': post_id
                        }
                    },
                    status=201
                )

        answer_id = response.json['data']['id']

        with freeze_time("2018.01.04 00:10"):
            with open('docs/source/monitoring/tutorial/http/post-answer-docs.http', 'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts/{}/documents?acc_token={}'.format(
                        monitoring_id, answer_id, tender_owner_token
                    ),
                    {
                        "data": {
                            'title': 'dolor.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    },
                    status=201
                )

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        with freeze_time("2018.01.04 01:05"):
            with open('docs/source/monitoring/tutorial/http/post-broker-publish.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {
                        "data": {
                            "title": "Dolor sit amet",
                            "description": "Lorem ipsum dolor sit amet.",
                            "documents": [{
                                'title': 'ipsum.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }]
                        }
                    },
                    status=201
                )

        post_broker_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.04 01:15"):
            with open('docs/source/monitoring/tutorial/http/post-broker-sas-answer.http', 'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts'.format(monitoring_id),
                    {
                        "data": {
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
                        }
                    },
                    status=201
                )

        with open('docs/source/monitoring/tutorial/http/posts-get.http', 'wt') as self.app.file_obj:
            self.app.get(
                '/monitorings/{}/posts'.format(monitoring_id),
                status=200
            )

        # CONCLUSION
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.05 00:00"):
            with open('docs/source/monitoring/tutorial/http/conclusion-wo-violations.http', 'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "conclusion": {
                                "violationOccurred": False,
                                "relatedParty": party_id
                            }
                        }
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json["data"]["conclusion"]["violationOccurred"], False)

        with freeze_time("2018.01.05 00:10"):
            with open('docs/source/monitoring/tutorial/http/conclusion-failed-required.http',
                      'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "conclusion": {
                                "violationOccurred": True,
                            }
                        }
                    },
                    status=422
                )

        self.assertEqual(len(response.json["errors"]), 1)

        with freeze_time("2018.01.05 00:15"):
            with open('docs/source/monitoring/tutorial/http/conclusion-full.http', 'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
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
                        }
                    }
                )
            self.assertEqual(response.status_code, 200)

        with freeze_time("2018.01.05 00:17"):
            with open('docs/source/monitoring/tutorial/http/conclusion-other-validation.http',
                      'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "conclusion": {
                                "violationType": ["documentsForm", "corruptionAwarded", "other"],
                            }
                        }
                    },
                    status=422
                )
                self.assertEqual(
                    response.json['errors'],
                    [{
                        u'description': {u'otherViolationType': [u'This field is required.']},
                        u'location': u'body', u'name': u'conclusion'
                    }])

        with freeze_time("2018.01.05 00:20"):
            with open('docs/source/monitoring/tutorial/http/conclusion-add-document.http', 'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/conclusion/documents'.format(monitoring_id),
                    {
                        "data": {
                            'title': 'sign.p7s',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/pkcs7-signature',
                        }
                    },
                    status=201
                )

        with freeze_time("2018.01.05 00:25"):
            with open('docs/source/monitoring/tutorial/http/conclusion-addressed.http', 'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "status": "addressed",
                        }
                    }
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["status"], "addressed")

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        with freeze_time("2018.01.06 00:00"):
            with open('docs/source/monitoring/tutorial/http/conclusion-post.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/posts?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {
                        "data": {
                            "title": "Sit amet",
                            "description": "Sit amet lorem ipsum dolor.",
                            "documents": [{
                                'title': 'dolor.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }]
                        }
                    },
                    status=201
                )

        post_conclusion_id = response.json['data']['id']

        with freeze_time("2018.01.03 00:10"):
            with open('docs/source/monitoring/tutorial/http/post-conclusion-add-document.http',
                      'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/posts/{}/documents?acc_token={}'.format(
                        monitoring_id, post_conclusion_id, tender_owner_token),
                    {
                        "data": {
                            'title': 'dolor.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }
                    },
                    status=201
                )

        # APPEAL
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        with freeze_time("2018.01.06 07:00"):
            with open('docs/source/monitoring/tutorial/http/appeal-post.http', 'wt') as self.app.file_obj:
                response = self.app.put_json(
                    '/monitorings/{}/appeal?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {
                        "data": {
                            "description": "Appeal description",
                            "documents": [{
                                'title': 'letter.doc',
                                'url': self.generate_docservice_url(),
                                'hash': 'md5:' + '0' * 32,
                                'format': 'application/msword',
                            }]
                        }
                    },
                )
                appeal_doc_id = response.json["data"]["documents"][0]["id"]

        another_document = {
            'title': 'another-letter.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
        }

        with freeze_time("2018.01.06 07:30"):
            with open('docs/source/monitoring/tutorial/http/appeal-post-again.http', 'wt') as self.app.file_obj:
                self.app.put_json(
                    '/monitorings/{}/appeal?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {
                        "data": {
                            "description": "Addition to the appeal description",
                            "documents": [another_document]
                        }
                    },
                    status=403
                )

        with freeze_time("2018.01.06 08:00"):
            with open('docs/source/monitoring/tutorial/http/appeal-post-doc.http', 'wt') as self.app.file_obj:
                self.app.post_json(
                    '/monitorings/{}/appeal/documents?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {"data": another_document},
                )

        with freeze_time("2018.01.06 08:15"):
            with open('docs/source/monitoring/tutorial/http/appeal-patch-doc.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}/appeal/documents/{}?acc_token={}'.format(
                        monitoring_id,
                        appeal_doc_id,
                        tender_owner_token
                    ),
                    {
                        "data": {
                            'title': 'letter(0).doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/json',
                        }
                    },
                )

        # ELIMINATION REPORT
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))

        with freeze_time("2018.01.07 00:00"):
            with open('docs/source/monitoring/tutorial/http/elimination-report-post.http', 'wt') as self.app.file_obj:
                response = self.app.put_json(
                    '/monitorings/{}/eliminationReport?acc_token={}'.format(monitoring_id, tender_owner_token),
                    {
                        "data": {
                            "description": "The procurement requirements have been fixed and the changes are attached.",
                            "documents": [
                                {
                                    'title': 'requirements.doc',
                                    'url': self.generate_docservice_url(),
                                    'hash': 'md5:' + '0' * 32,
                                    'format': 'application/msword',
                                }
                            ],
                        }
                    },
                )

        self.assertEqual(response.status_code, 200)

        # ELIMINATION RESOLUTION
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.09 00:00"):
            with open('docs/source/monitoring/tutorial/http/elimination-resolution-post.http',
                      'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
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
                        }
                    },
                )

        with freeze_time("2018.01.25 00:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-to-completed.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "status": "completed",
                        }
                    },
                    status=200
                )

        with freeze_time("2018.01.25 01:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-documents.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/monitorings/{}/documents'.format(monitoring_id),
                    {
                        "data": {
                            "url": self.generate_docservice_url(),
                            "title": "sign.p7s",
                            "hash": "md5:00000000000000000000000000000000",
                            "format": "application/ms-word"
                        }
                    },
                    status=201
                )

        doc_id = response.json["data"]["id"]
        with freeze_time("2018.01.25 01:30"):
            with open('docs/source/monitoring/tutorial/http/monitoring-documents-put.http', 'wt') as self.app.file_obj:
                doc_hash = "1" * 32
                self.app.put_json(
                    '/monitorings/{}/documents/{}'.format(monitoring_id, doc_id),
                    {
                        "data": {
                            "url": self.generate_docservice_url(doc_hash=doc_hash),
                            "title": "sign_updated.p7s",
                            "hash": "md5:{}".format(doc_hash),
                            "format": "application/ms-word",
                        }
                    },
                    status=200
                )

        with freeze_time("2018.01.25 01:32"):
            with open('docs/source/monitoring/tutorial/http/monitoring-documents-get.http', 'wt') as self.app.file_obj:
                self.app.get(
                    '/monitorings/{}/documents/{}'.format(monitoring_id, doc_id),
                    status=200
                )

        with freeze_time("2018.01.25 01:35"):
            with open('docs/source/monitoring/tutorial/http/monitoring-documents-patch.http',
                      'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}/documents/{}'.format(monitoring_id, doc_id),
                    {
                        "data": {
                            "title": "sign.p7s",
                            "format": "application/pkcs7-signature",
                            "description": "Description? Wow!",
                            "language": "It's some kind of Elvish.I can't read it.",
                        }
                    },
                    status=200
                )

        with freeze_time("2018.01.25 01:40"):
            with open('docs/source/monitoring/tutorial/http/monitoring-documents-get-collection.http',
                      'wt') as self.app.file_obj:
                self.app.get(
                    '/monitorings/{}/documents'.format(monitoring_id),
                    status=200
                )

    def test_monitoring_life_cycle_with_no_violations(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/monitorings',
                {
                    "data": {
                        "tender_id": self.uuid().hex,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"],
                        "parties": [self.party]
                    }
                },
                status=201
            )

        monitoring_id = response.json["data"]["id"]
        party_id = response.json["data"]["parties"][0]["id"]

        with freeze_time("2018.01.02 00:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-publish.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
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
                        }
                    },
                    status=200
                )

        with freeze_time("2018.01.03 00:10"):
            self.app.post_json(
                '/monitorings/{}/posts'.format(monitoring_id),
                {
                    "data": {
                        "title": "Lorem ipsum",
                        "description": "Lorem ipsum dolor sit amet.",
                        "documents": [{
                            'title': 'ipsum.doc',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/msword',
                        }],
                        "relatedParty": party_id
                    }
                },
                status=201
            )

        with freeze_time("2018.01.04 00:00"):
            self.app.patch_json(
                '/monitorings/{}'.format(monitoring_id),
                {
                    "data": {
                        "conclusion": {
                            "violationOccurred": False,
                            "relatedParty": party_id
                        },
                        "status": "declined"
                    }
                },
            )

        with freeze_time("2018.01.11 00:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-to-closed.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "status": "closed",
                        }
                    }
                )

    def test_monitoring_life_cycle_stopped(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/monitorings',
                {
                    "data": {
                        "tender_id": self.uuid().hex,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"],
                        "parties": [self.party]
                    }
                },
                status=201
            )

        monitoring_id = response.json["data"]["id"]
        party_id = response.json["data"]["parties"][0]["id"]

        with freeze_time("2018.01.02 00:00"):
            self.app.patch_json(
                '/monitorings/{}'.format(monitoring_id),
                {
                    "data": {
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
                    }
                },
                status=200
            )

        with freeze_time("2018.01.03 00:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-to-stopped.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "cancellation": {
                                "description": "Complaint was created",
                                "relatedParty": party_id
                            },
                            "status": "stopped",
                        }
                    }
                )

    def test_monitoring_life_cycle_cancelled(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/monitorings',
                {
                    "data": {
                        "tender_id": self.uuid().hex,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"],
                        "parties": [self.party]
                    }
                },
                status=201
            )

        monitoring_id = response.json["data"]["id"]
        party_id = response.json["data"]["parties"][0]["id"]

        with freeze_time("2018.01.03 00:00"):
            with open('docs/source/monitoring/tutorial/http/monitoring-to-cancelled.http', 'wt') as self.app.file_obj:
                self.app.patch_json(
                    '/monitorings/{}'.format(monitoring_id),
                    {
                        "data": {
                            "cancellation": {
                                "description": "Some reason",
                                "relatedParty": party_id
                            },
                            "status": "cancelled",
                        }
                    }
                )


@freeze_time("2018.01.01 00:00")
class FeedDocsTest(BaseMonitoringWebTest):

    def setUp(self):
        super(FeedDocsTest, self).setUp()

        for i in range(5):
            self.create_active_monitoring()

    def test_changes_feed(self):
        with open('docs/source/monitoring/feed/http/changes-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&limit=3&opt_fields=reasons')

            self.assertEqual(len(response.json["data"]), 3)
            self.assertIn("next_page", response.json)

        with open('docs/source/monitoring/feed/http/changes-feed-next.http', 'wt') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 2)
            self.assertIn("next_page", response.json)

        with open('docs/source/monitoring/feed/http/changes-feed-last.http', 'wt') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 0)
            self.assertIn("next_page", response.json)

        self.create_active_monitoring()

        with open('docs/source/monitoring/feed/http/changes-feed-new.http', 'wt') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)

        next_url = response.json["next_page"]["path"]

        with open('docs/source/monitoring/feed/http/changes-feed-new-next.http', 'wt') as self.app.file_obj:
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 0)
            self.assertIn("next_page", response.json)

        self.create_active_monitoring()

        with open('docs/source/monitoring/feed/http/changes-feed-new-last.http', 'wt') as self.app.file_obj:
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)


@freeze_time("2018.01.01 00:00")
class PrivateFeedDocsTest(BaseMonitoringWebTest):

    def create_items(self, **kwargs):
        self.tender_id = '13c14e6a15b24e1a982310f262e18e7a'
        kwargs.update(tender_id=self.tender_id)

        self.create_monitoring(**kwargs)  # draft

        self.create_monitoring(**kwargs)  # cancelled

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {
                "data": {
                    "cancellation": {
                        "description": "Some reason",
                    },
                    "status": "cancelled",
                }
            }
        )

        self.create_active_monitoring(**kwargs)  # active

    def test_feed_public(self):
        self.create_items()

        with open('docs/source/monitoring/feed/http/public-changes-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&opt_fields=status')

            self.assertEqual(len(response.json["data"]), 1)

        with open('docs/source/monitoring/feed/http/public-date-modified-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?opt_fields=status')

            self.assertEqual(len(response.json["data"]), 1)

        with open('docs/source/monitoring/feed/http/public-tender-monitorings.http', 'wt') as self.app.file_obj:
            response = self.app.get('/tenders/{}/monitorings'.format(self.tender_id))

            self.assertEqual(len(response.json["data"]), 1)

    def test_feed_public_test(self):
        self.create_items(mode="test")

        with open('docs/source/monitoring/feed/http/public-test-changes-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=test&feed=changes&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 1)

        with open('docs/source/monitoring/feed/http/public-test-date-modified-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=test&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 1)

        with open('docs/source/monitoring/feed/http/public-test-tender-monitorings.http', 'wt') as self.app.file_obj:
            response = self.app.get('/tenders/{}/monitorings?mode=test&opt_fields=mode'.format(self.tender_id))

            self.assertEqual(len(response.json["data"]), 1)

    def test_feed_private(self):
        self.create_items()

        with open('docs/source/monitoring/feed/http/private-changes-feed-forbidden.http', 'wt') as self.app.file_obj:
            self.app.get('/monitorings?feed=changes&mode=real_draft&opt_fields=status', status=403)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with open('docs/source/monitoring/feed/http/private-changes-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&mode=real_draft&opt_fields=status')

            self.assertEqual(len(response.json["data"]), 3)

        with open('docs/source/monitoring/feed/http/private-date-modified-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=real_draft&opt_fields=status')

            self.assertEqual(len(response.json["data"]), 3)

        with open('docs/source/monitoring/feed/http/private-tender-monitorings.http', 'wt') as self.app.file_obj:
            response = self.app.get('/tenders/{}/monitorings?mode=draft'.format(self.tender_id))

            self.assertEqual(len(response.json["data"]), 3)

    def test_feed_private_test(self):
        self.create_items(mode="test")

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with open('docs/source/monitoring/feed/http/private-test-changes-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?feed=changes&mode=all_draft&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 3)

        with open('docs/source/monitoring/feed/http/private-test-date-modified-feed.http', 'wt') as self.app.file_obj:
            response = self.app.get('/monitorings?mode=all_draft&opt_fields=status%2Cmode')

            self.assertEqual(len(response.json["data"]), 3)


class MonitoringByTenderResourceTest(BaseMonitoringWebTest):

    def setUp(self):
        super(MonitoringByTenderResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://public-docs-sandbox.prozorro.gov.ua'

    def test_tutorial(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        tender_id = "580997bb06674235801d75f2f6e6c6c6"

        with freeze_time("2018.01.01 00:00"):
            self.create_monitoring(tender_id=tender_id)
            self.app.patch_json(
                '/monitorings/{}'.format(self.monitoring_id),
                {"data": {
                    "decision": {"description": "text"},
                    "status": "active",
                }}
            )

        with freeze_time("2018.01.01 00:01"):
            self.create_monitoring(tender_id=tender_id)
            self.app.patch_json(
                '/monitorings/{}'.format(self.monitoring_id),
                {"data": {
                    "decision": {"description": "text"},
                    "status": "active",
                }}
            )

        with freeze_time("2018.01.01 00:02"):
            file = 'docs/source/monitoring/monitorings_by_tender/http/monitorings-by-tender-id.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/tenders/{}/monitorings'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 2)

        with freeze_time("2018.01.01 00:03"):
            file = 'docs/source/monitoring/monitorings_by_tender/http/monitorings-by-tender-id-opt-fields.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/tenders/{}/monitorings?opt_fields=status'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 2)

        with freeze_time("2018.01.01 00:03"):
            file = 'docs/source/monitoring/monitorings_by_tender/http/monitorings-by-tender-id-pagination.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/tenders/{}/monitorings?limit=1&page2'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 1)



class InspectionResourceTest(BaseInspectionWebTest):

    def setUp(self):
        super(InspectionResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://public-docs-sandbox.prozorro.gov.ua'

    def test_tutorial(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with open('docs/source/inspection/tutorial/http/inspection-list-empty.http', 'wt') as self.app.file_obj:
            response = self.app.get('/inspections', status=200)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data'], [])

        with freeze_time("2018.01.01 00:00"):
            with open('docs/source/inspection/tutorial/http/inspection-post.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/inspections',
                    {
                        "data": {

                            "monitoring_ids": [
                                "a6b2b18977f24277b238c7b7a5342b1d",
                                "580997bb06674235801d75f2f6e6c6c6",
                                "2c5cc4a289d747a5b8dacd72adaea4d9",
                            ],
                            "description": "Inspection is an official visit to a building or organization to check "
                                           "that everything is satisfactory and that rules are being obeyed",
                        }
                    }
                )
        inspection_id = response.json["data"]["id"]
        self.assertEqual(response.status, '201 Created')

        with freeze_time("2018.01.01 00:01"):
            with open('docs/source/inspection/tutorial/http/inspection-document-post.http', 'wt') as self.app.file_obj:
                response = self.app.post_json(
                    '/inspections/{}/documents'.format(inspection_id),
                    {
                        "data": {
                            'title': 'doc.txt',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'plain/text',
                        }
                    }
                )
        document_id = response.json["data"]["id"]
        self.assertEqual(response.status, '201 Created')

        with freeze_time("2018.01.01 00:02"):
            with open('docs/source/inspection/tutorial/http/inspection-document-put.http', 'wt') as self.app.file_obj:
                response = self.app.put_json(
                    '/inspections/{}/documents/{}'.format(inspection_id, document_id),
                    {
                        "data": {
                            'title': 'doc(1).json',
                            'url': self.generate_docservice_url(),
                            'hash': 'md5:' + '0' * 32,
                            'format': 'application/json',
                        }
                    }
                )
        self.assertEqual(response.status, '200 OK')

        with freeze_time("2018.01.01 00:03"):
            with open('docs/source/inspection/tutorial/http/inspection-patch.http', 'wt') as self.app.file_obj:
                response = self.app.patch_json(
                    '/inspections/{}'.format(inspection_id),
                    {
                        "data": {
                            "description": "I regretted my decision",
                            "monitoring_ids": [
                                "a6b2b18977f24277b238c7b7a5342b1d",
                                "580997bb06674235801d75f2f6e6c6c6",
                            ]
                        }
                    }
                )
        self.assertEqual(response.status, '200 OK')


class InspectionsByMonitoringResourceTest(BaseInspectionWebTest):

    def setUp(self):
        super(InspectionsByMonitoringResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://public-docs-sandbox.prozorro.gov.ua'

    def test_tutorial(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        monitoring_id = "580997bb06674235801d75f2f6e6c6c6"

        with freeze_time("2018.01.01 00:00"):
            response = self.app.post_json(
                '/inspections',
                {
                    "data": {
                        "monitoring_ids": [monitoring_id],
                        "description": "La-la",
                    }
                }
            )
        self.assertEqual(response.status, '201 Created')

        with freeze_time("2018.01.01 00:01"):
            response = self.app.post_json(
                '/inspections',
                {
                    "data": {
                        "monitoring_ids": [monitoring_id],
                        "description": "Inspection is an official visit to a building or organization to check "
                                       "that everything is satisfactory and that rules are being obeyed",
                    }
                }
            )
        self.assertEqual(response.status, '201 Created')

        with freeze_time("2018.01.01 00:02"):
            file = 'docs/source/inspection/inspections_by_monitoring/http/inspections-by-monitoring_id.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/monitorings/{}/inspections'.format(monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 2)

        with freeze_time("2018.01.01 00:03"):
            file = 'docs/source/inspection/inspections_by_monitoring/http/inspections-by-monitoring_id-opt_fields.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/monitorings/{}/inspections?opt_fields=description'.format(monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 2)

        with freeze_time("2018.01.01 00:03"):
            file = 'docs/source/inspection/inspections_by_monitoring/http/inspections-by-monitoring_id-pagination.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/monitorings/{}/inspections?limit=1&page=2'.format(monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 1)


class RequestResourceTest(BaseRequestWebTest):

    def setUp(self):
        super(RequestResourceTest, self).setUp()
        self.app.app.registry.docservice_url = "http://public-docs-sandbox.prozorro.gov.ua"

    def test_tutorial(self):
        with open("docs/source/request/tutorial/http/request-list-empty.http", "wt") as self.app.file_obj:
            response = self.app.get("/requests", status=200)
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.json["data"], [])

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        with freeze_time("2018.01.01 00:00"):
            with open("docs/source/request/tutorial/http/request-post.http", "wt") as self.app.file_obj:
                response = self.app.post_json(
                    "/requests",
                    {
                        "data": {
                            "tenderId": "f" * 32,
                            "description": "Yo-ho-ho",
                            "violationType": VIOLATION_TYPE_CHOICES,
                            "parties": [
                                {
                                    "name": "party name",
                                    "address": {
                                        "streetAddress": "test street address",
                                        "locality": "test locality",
                                        "region": "test region",
                                        "postalCode": "test postalCode",
                                        "countryName": "test country",
                                    },
                                    "contactPoint": {
                                        "email": "test@example.com"
                                    }
                                }
                            ],
                            "documents": [
                                {
                                    "title": "doc.txt",
                                    "url": self.generate_docservice_url(),
                                    "hash": "md5:" + "0" * 32,
                                    "format": "plain/text",
                                }
                            ]
                        }
                    }
                )
        request_id = response.json["data"]["id"]
        self.assertEqual(response.status, "201 Created")

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        with freeze_time("2018.01.01 00:01"):
            with open("docs/source/request/tutorial/http/request-document-post.http", "wt") as self.app.file_obj:
                response = self.app.post_json(
                    "/requests/{}/documents".format(request_id),
                    {
                        "data": {
                            "title": "doc(1).txt",
                            "url": self.generate_docservice_url(),
                            "hash": "md5:" + "0" * 32,
                            "format": "plain/text",
                        }
                    }
                )
        document_id = response.json["data"]["id"]
        self.assertEqual(response.status, "201 Created")

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        with freeze_time("2018.01.01 00:02"):
            with open("docs/source/request/tutorial/http/request-document-put.http", "wt") as self.app.file_obj:
                response = self.app.put_json(
                    "/requests/{}/documents/{}".format(request_id, document_id),
                    {
                        "data": {
                            "title": "doc(2).json",
                            "url": self.generate_docservice_url(),
                            "hash": "md5:" + "0" * 32,
                            "format": "application/json",
                        }
                    }
                )
        self.assertEqual(response.status, "200 OK")

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        with freeze_time("2018.01.01 00:03"):
            with open("docs/source/request/tutorial/http/request-patch.http", "wt") as self.app.file_obj:
                response = self.app.patch_json(
                    "/requests/{}".format(request_id),
                    {
                        "data": {
                            "answer": "There is my answer",
                        }
                    }
                )
        self.assertEqual(response.status, "200 OK")

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        with freeze_time("2018.01.01 00:03"):
            with open("docs/source/request/tutorial/http/request-patch-forbidden.http", "wt") as self.app.file_obj:
                response = self.app.patch_json(
                    "/requests/{}".format(request_id),
                    {
                        "data": {
                            "answer": "There is my another answer",
                        }
                    },
                    status=403
                )
        self.assertEqual(response.status, "403 Forbidden")

        self.app.authorization = None
        with open("docs/source/request/tutorial/http/request-get-no-auth.http", "wt") as self.app.file_obj:
            response = self.app.get("/requests/{}".format(request_id))
        self.assertNotIn("address", response.json["data"]["parties"][0])
        self.assertEqual(response.status, "200 OK")

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        with open("docs/source/request/tutorial/http/request-get-sas.http", "wt") as self.app.file_obj:
            response = self.app.get("/requests/{}".format(request_id))
        self.assertIn("address", response.json["data"]["parties"][0])
        self.assertEqual(response.status, "200 OK")

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        with freeze_time("2018.02.01 00:00"):
            with open("docs/source/request/tutorial/http/request-post-not-answered.http", "wt") as self.app.file_obj:
                response = self.app.post_json(
                    "/requests",
                    {
                        "data": {
                            "tenderId": "f" * 32,
                            "description": "Yo-ho-ho",
                            "violationType": VIOLATION_TYPE_CHOICES,
                            "parties": [
                                {
                                    "name": "party name",
                                    "address": {
                                        "streetAddress": "test street address",
                                        "locality": "test locality",
                                        "region": "test region",
                                        "postalCode": "test postalCode",
                                        "countryName": "test country",
                                    },
                                    "contactPoint": {
                                        "email": "test@example.com"
                                    }
                                }
                            ],
                            "documents": [
                                {
                                    "title": "doc.txt",
                                    "url": self.generate_docservice_url(),
                                    "hash": "md5:" + "0" * 32,
                                    "format": "plain/text",
                                }
                            ]
                        }
                    }
                )
        request_id = response.json["data"]["id"]
        self.assertEqual(response.status, "201 Created")

        self.app.authorization = None
        with open("docs/source/request/tutorial/http/requests-list.http", "wt") as self.app.file_obj:
            response = self.app.get("/requests?opt_fields=answer".format(request_id))

        with open("docs/source/request/tutorial/http/requests-list-answered.http", "wt") as self.app.file_obj:
            response = self.app.get("/requests?mode=real_answered&opt_fields=answer".format(request_id))



class RequestByTenderResourceTest(BaseRequestWebTest):

    def setUp(self):
        super(RequestByTenderResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://public-docs-sandbox.prozorro.gov.ua'

    def test_tutorial(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        tender_id = "580997bb06674235801d75f2f6e6c6c6"

        with freeze_time("2018.01.01 00:00"):
            self.create_request(tenderId=tender_id, description="First request")

        with freeze_time("2018.01.01 00:01"):
            self.create_request(tenderId=tender_id, description="Second request")

        with freeze_time("2018.01.01 00:02"):
            file = 'docs/source/request/requests_by_tender/http/requests-by-tender-id.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/tenders/{}/requests'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 2)

        with freeze_time("2018.01.01 00:03"):
            file = 'docs/source/request/requests_by_tender/http/requests-by-tender-id-opt-fields.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/tenders/{}/requests?opt_fields=description'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 2)

        with freeze_time("2018.01.01 00:03"):
            file = 'docs/source/request/requests_by_tender/http/requests-by-tender-id-pagination.http'
            with open(file, 'wt') as self.app.file_obj:
                response = self.app.get('/tenders/{}/requests?limit=1&page2'.format(tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json["data"]), 1)
