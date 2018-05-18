from freezegun import freeze_time
from openprocurement.api.constants import TZ
from openprocurement.audit.api.constraints import MONITORING_TIME
from openprocurement.audit.api.tests.base import BaseWebTest
import unittest
from datetime import datetime, timedelta
from openprocurement.tender.core.utils import calculate_business_date


class MonitoringResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitoringResourceTest, self).setUp()
        self.create_monitoring()

    def test_get(self):
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["id"], self.monitoring_id)

    def test_patch_forbidden_url(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"status": "active"},
            status=403
        )

    def test_patch_without_decision(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {"status": "active"}},
            status=422
        )

    @freeze_time('2018-01-01T12:00:00.000000+03:00')
    def test_patch_to_active(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        now_date = datetime.now(TZ)
        end_date = calculate_business_date(now_date, MONITORING_TIME, working_days=True)
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
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
            '/monitorings/{}'.format(self.monitoring_id),
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

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {
                    "description": "text_changed",
                }
            }},
            status=422
        )

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "draft"
            }},
            status=422
        )

class ActiveMonitoringResourceTest(BaseWebTest):
    def setUp(self):
        super(ActiveMonitoringResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active",
                "decision": {
                    "description": "text",
                    "date": (datetime.now() + timedelta(days=2)).isoformat()
                }
            }}
        )

    def test_patch_to_declined(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                },
                "status": "declined",
            }},
        )

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "declined")

    def test_patch_to_declined_if_violation_occurred(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": "corruptionProcurementMethodType",
                },
                "status": "declined",
            }},
            status=403
        )

        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')

    def test_patch_to_addressed(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": "corruptionProcurementMethodType",
                },
                "status": "addressed",
            }},
        )

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "addressed")

    def test_patch_to_addressed_if_no_violation_occurred(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                },
                "status": "addressed",
            }},
            status=403
        )

        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')

    def test_patch_to_stopped(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "stopped",
                "stopping": {
                    "description": "Whisper words of wisdom - let it be."
                }
            }},
        )

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "stopped")


class DeclinedMonitoringResourceTest(BaseWebTest):
    def setUp(self):
        super(DeclinedMonitoringResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_token, ''))
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active",
                "decision": {
                    "description": "text",
                    "date": (datetime.now() + timedelta(days=2)).isoformat()
                }
            }}
        )
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                },
                "status": "declined",
            }},
        )

    def test_patch_to_closed(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "closed",
            }},
        )

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "closed")

def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitoringResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
