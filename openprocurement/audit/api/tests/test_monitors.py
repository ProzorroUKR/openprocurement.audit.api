from openprocurement.audit.api.tests.base import BaseWebTest
import unittest


class MonitorsEmptyListingResourceTest(BaseWebTest):

    def test_get(self):
        response = self.app.get('/monitors')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_post_monitor_without_authorisation(self):
        self.app.post_json('/monitors', {}, status=403)
        
    def test_post_monitor_broker(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        self.app.post_json('/monitors', {}, status=403)

    def test_post_monitor_sas_empty_body(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitors', {}, status=422)
        self.assertEqual(len(response.json.get("errors", [])), 1)
        self.assertEqual(response.json["errors"][0]["description"], "Data not available")

    def test_post_monitor_sas_empty_data(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitors', {"data": {}}, status=422)
        self.assertEqual(response.json["errors"][0]["name"], "tender_id")
        self.assertEqual(response.json["errors"][0]["description"], ["This field is required."])

    def test_post_monitor_sas(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitors', {"data": {"tender_id": "f" * 32}}, status=201)

        self.assertIn("access", response.json)
        self.assertIn("token", response.json["access"])

        self.assertIn("data", response.json)
        self.assertEqual(
            set(response.json["data"]),
            {"id", "status", "tender_id", "owner", "dateModified", "dateCreated"}
        )
        self.assertEqual(response.json["data"]["status"], "draft")


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorsEmptyListingResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
