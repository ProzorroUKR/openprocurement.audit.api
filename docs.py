from webtest import TestApp
from datetime import datetime
import openprocurement.audit.api.tests.base as base_test
import ConfigParser
import json
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


class MonitorsEmptyListingResourceTest(base_test.BaseWebTest):

    def setUp(self):
        self.app = DumpsTestAppwebtest(
            "config:tests.ini", relative_to=os.path.dirname(base_test.__file__))
        self.app.RequestClass = base_test.PrefixedRequestClass
        self.app.authorization = ('Basic', ('broker', ''))
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db

        config = ConfigParser.RawConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'openprocurement/audit/api/tests/auth.ini'))
        self.broker_token = config.get("brokers", "broker")
        self.sas_token = config.get("sas", "test_sas")

    def test_monitor_life_cycle(self):

        # CREATION
        with open('docs/source/http/empty-listing.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitors')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data'], [])

        with open('docs/source/http/post-monitor-empty-body.http', 'w') as self.app.file_obj:
            self.app.authorization = ('Basic', (self.sas_token, ''))
            self.app.post_json('/monitors', {"data": {}}, status=422)

        with open('docs/source/http/post-monitor.http', 'w') as self.app.file_obj:
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

        with open('docs/source/http/listing-with-object.http', 'w') as self.app.file_obj:
            response = self.app.get('/monitors')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)

        # PUBLISHING
        with open('docs/source/http/publish-monitor-wo-decision.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {"status": "active"}},
                status=403
            )

        with open('docs/source/http/publish-monitor.http', 'w') as self.app.file_obj:
            self.app.patch_json(
                '/monitors/{}?acc_token={}'.format(monitor_id, monitor_token),
                {"data": {
                    "status": "active",
                    "decision": {
                        "description": "text",
                        "date": datetime.now().isoformat()
                    }
                }},
                status=200
            )





