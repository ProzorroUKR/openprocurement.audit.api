from freezegun import freeze_time
from openprocurement.api import utils
from openprocurement.api.utils import generate_id
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

        self.uuid_counter = 0

        def generate_test_uuid():
            self.uuid_counter += 1
            return uuid.uuid3(uuid.UUID(int=0), self.id() + str(self.uuid_counter))

        self.uuid4_patch = mock.patch('openprocurement.api.utils.uuid4', side_effect=generate_test_uuid)
        self.uuid4_patch.start()

    def tearDown(self):
        self.uuid4_patch.stop()
        super(BaseDocWebTest, self).tearDown()


class OptionsResourceTest(BaseDocWebTest):

    def test_monitor_list_options_query_params(self):
        with open('docs/source/options/http/monitors-with-options.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', (self.sas_token, ''))
            response = self.app.post_json(
                '/monitors',
                {
                    "options": {"pretty": True},
                    "data": {
                        "tender_id": "f" * 32,
                        "reasons": ["public", "fiscal"],
                        "procuringStages": ["awarding", "contracting"]
                    }
                },
                status=201
            )
        self.assertEqual(response.status, '201 Created')

        with open('docs/source/options/http/monitors-with-options-query-params.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitors?opt_fields=status')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)


class MonitorsResourceTest(BaseDocWebTest, base_test.DSWebTestMixin):
    def setUp(self):
        super(MonitorsResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://docs-sandbox.openprocurement.org'

    def test_monitor_life_cycle(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))

        with open('docs/source/tutorial/http/monitors-empty.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitors', status=200)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data'], [])

        with open('docs/source/tutorial/http/monitor-post-empty-body.http', 'w') as self.app.file_obj:
            self.app.post_json('/monitors', {"data": {}}, status=422)

        with open('docs/source/tutorial/http/monitor-post.http', 'w') as self.app.file_obj:
            response = self.app.post_json(
                '/monitors',
                {"data": {
                    "tender_id": "f" * 32,
                    "reasons": ["public", "fiscal"],
                    "procuringStages": ["awarding", "contracting"]
                }},
                status=201
            )

        monitor_id = response.json["data"]["id"]
        monitor_token = response.json["access"]["token"]

        with open('docs/source/tutorial/http/monitors-with-object.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitors')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        with open('docs/source/tutorial/http/monitor-publish-wo-decision.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {"status": "active"}},
                status=403
            )

        # PUBLISH
        with open('docs/source/tutorial/http/monitor-publish-first-step.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
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

        with open('docs/source/tutorial/http/monitor-publish-add-document.http', 'w') as self.app.file_obj:
            self.app.post_json(
                '/monitors/{}/decision/documents?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {
                    'title': 'dolor.doc',
                    'url': self.generate_docservice_url(),
                    'hash': 'md5:' + '0' * 32,
                    'format': 'application/msword',
                }},
                status=201
            )

        with open('docs/source/tutorial/http/monitor-publish-second-step.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {
                    "status": "active"
                }},
                status=200
            )

        with open('docs/source/tutorial/http/monitor-publish-change.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {
                    "decision": {
                        "description": "another_text",
                    }
                }},
                status=403
            )

        # DIALOGUE
        with open('docs/source/tutorial/http/dialogue-publish.http', 'w') as self.app.file_obj:
            response = self.app.post_json(
                '/monitors/{}/dialogues?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {
                    "title": "Lorem ipsum",
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

        dialogue_id = response.json['data']['id']
        dialogue_token = response.json['access']['token']

        with open('docs/source/tutorial/http/dialogue-publish-add-document.http', 'w') as self.app.file_obj:
            self.app.post_json(
                '/monitors/{}/dialogues/{}/documents?acc_token={}'.format(monitor_id, dialogue_id, dialogue_token),
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
                '/monitors/{}/dialogues/{}/documents'.format(monitor_id, dialogue_id, dialogue_token),
                status=200
            )

    def test_monitor_creation_fast(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))

        response = self.app.post_json(
            '/monitors',
            {"data": {
                "tender_id": "f" * 32,
                "reasons": ["public", "fiscal"],
                "procuringStages": ["awarding", "contracting"]
            }},
            status=201
        )

        monitor_id = response.json["data"]["id"]
        monitor_token = response.json["access"]["token"]

        with open('docs/source/tutorial/http/monitor-publish.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
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


class FeedDocsTest(BaseDocWebTest):

    def setUp(self):
        super(FeedDocsTest, self).setUp()

        for i in range(5):
            self.create_monitor()

    def test_changes_feed(self):
        with open('docs/source/feed/http/changes-feed.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitors?feed=changes&limit=3&opt_fields=reasons')

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

        self.create_monitor()

        with open('docs/source/feed/http/changes-feed-new.http', 'w') as self.app.file_obj:
            response = self.app.get(response.json["next_page"]["path"])

            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)

        next_url = response.json["next_page"]["path"]

        with open('docs/source/feed/http/changes-feed-new-next.http', 'w') as self.app.file_obj:
            print(next_url)
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 0)
            self.assertIn("next_page", response.json)

        self.create_monitor()

        # TODO: why doesn't this make the tender be shown on the next page?
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {'data': {"reasons": ['media', 'public']}}
        )

        with open('docs/source/feed/http/changes-feed-new-last.http', 'w') as self.app.file_obj:
            response = self.app.get(next_url)
            self.assertEqual(len(response.json["data"]), 1)
            self.assertIn("next_page", response.json)
