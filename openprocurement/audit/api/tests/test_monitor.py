from openprocurement.audit.api.tests.base import BaseWebTest
import unittest


class MonitorResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitorResourceTest, self).setUp()
        self.create_monitor()

    def test_get(self):
        response = self.app.get('/monitors/{}'.format(self.monitor_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["id"], self.monitor_id)

    def test_patch_forbidden_url(self):
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"status": "active"},
            status=403
        )

    def test_patch_without_acc_token(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {"status": "active"}},
            status=403
        )

    def test_patch(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitors/{}?acc_token={}'.format(self.monitor_id, self.monitor_token),
            {"data": {"status": "active"}}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["id"], self.monitor_id)
        self.assertEqual(response.json['data']["status"], "active")


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
