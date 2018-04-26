from freezegun import freeze_time
from openprocurement.api.constants import TZ
from openprocurement.audit.api.constraints import MONITORING_TIME
from openprocurement.audit.api.tests.base import BaseWebTest
import unittest
from datetime import datetime, timedelta
from openprocurement.tender.core.utils import calculate_business_date


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

    def test_patch_without_decision(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {"status": "active"}},
            status=403
        )

    @freeze_time('2018-01-01T12:00:00.000000+03:00')
    def test_patch_to_active(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        now_date = datetime.now(TZ)
        end_date = calculate_business_date(now_date, MONITORING_TIME, working_days=True)
        response = self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "status": "active",
                "decision": {
                    "description": "text",
                    "date": (now_date - timedelta(days=2)).isoformat()
                }
            }}
        )

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["monitoringPeriod"]["startDate"], now_date.isoformat())
        self.assertEqual(response.json['data']["monitoringPeriod"]["endDate"], end_date.isoformat())

    def test_patch_to_active_already_in_active(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "status": "active",
                "decision": {
                    "description": "text",
                    "date": (datetime.now() + timedelta(days=2)).isoformat()
                }
            }}
        )
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json(
            '/monitors/{}'.format(self.monitor_id),
            {"data": {
                "decision": {
                    "description": "text_changed",
                }
            }},
            status=403
        )
        self.assertEqual(response.status, '403 Forbidden')


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
