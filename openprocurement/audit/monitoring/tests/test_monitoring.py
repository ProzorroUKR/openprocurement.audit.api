import unittest

from dateorro import calc_working_datetime, calc_datetime
from datetime import datetime, timedelta
from freezegun import freeze_time
from parameterized import parameterized

from openprocurement.audit.api.constants import MONITORING_TIME, TZ, SANDBOX_MODE, WORKING_DAYS
from openprocurement.audit.monitoring.tests.base import BaseWebTest
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names
from openprocurement.audit.monitoring.utils import get_monitoring_accelerator


def masking_monitoring(self):
    # mask as admin
    self.app.authorization = ('Basic', (self.admin_name, self.admin_pass))
    response = self.app.patch_json(
        '/monitorings/{}'.format(self.monitoring_id),
        {"data": {"is_masked": True}},
    )
    self.assertTrue(response.json['data']["is_masked"])
    tender_id = response.json['data']["tender_id"]

    # see masked
    response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
    self.assertTrue(response.json['data']["is_masked"])
    if "decision" in response.json['data']:
        self.assertEqual(response.json['data']["decision"]["description"], "0000")

        # get listing
        response = self.app.get('/monitorings?opt_fields=decision,tender_id')
        monitoring = response.json["data"][0]
        self.assertEqual(monitoring["id"], self.monitoring_id)
        self.assertNotIn("decision", monitoring)

        # get listing by tender
        response = self.app.get(f'/tenders/{tender_id}/monitorings?opt_fields=decision')
        monitoring = response.json["data"][0]
        self.assertEqual(monitoring["id"], self.monitoring_id)
        self.assertEqual(monitoring["decision"]["description"], "0000")

        # get decision directly
        response = self.app.get(f'/monitorings/{self.monitoring_id}/decision')
        self.assertEqual(response.json['data']["description"], "0000")


@freeze_time('2018-01-01T09:00:00+02:00')
class MonitoringResourceTest(BaseWebTest):

    def setUp(self):
        super(MonitoringResourceTest, self).setUp()
        self.create_monitoring()

    def test_get(self):
        response = self.app.get('/monitorings/{}'.format(self.monitoring_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["id"], self.monitoring_id)

    def test_get_not_found(self):
        response = self.app.get('/monitorings/{}'.format('some_id'), status=404)
        self.assertEqual(response.status_code, 404)

    def test_patch_forbidden_url(self):
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"status": "active"},
            status=403
        )

    def test_patch_without_decision(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {"status": "active"}},
            status=422
        )
        self.assertEqual(('body', 'decision'), next(get_errors_field_names(response, 'This field is required.')))

    @freeze_time('2018-01-01T12:00:00.000000+02:00')
    def test_patch_nothing(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        now_date = datetime.now(TZ)
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "procuringStages":  ["planning"]
            }}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotEqual(response.json['data']["dateModified"], now_date.isoformat())
        self.assertEqual(response.json['data']["dateModified"], "2018-01-01T09:00:00+02:00")

    @freeze_time('2018-01-01T12:00:00.000000+02:00')
    def test_patch_to_active(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        context = self.acceleration if SANDBOX_MODE else {}
        accelerator = get_monitoring_accelerator(context)

        now_date = datetime.now(TZ)
        if accelerator:
            end_date = calc_datetime(
                now_date,
                MONITORING_TIME,
                accelerator=accelerator
            )
        else:
            end_date = calc_working_datetime(
                now_date,
                MONITORING_TIME,
                midnight=True,
                calendar=WORKING_DAYS
            )
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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["monitoringPeriod"]["startDate"], now_date.isoformat())
        self.assertEqual(response.json['data']["dateModified"], now_date.isoformat())
        self.assertEqual(response.json['data']["monitoringPeriod"]["endDate"], end_date.isoformat())

    def test_patch_risk_indicators_forbidden(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "riskIndicators": ["some_new_ids", 'fooBar']
            }},
            status=422
        )

    def test_patch_to_active_already_in_active(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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
        self.assertEqual(response.status_code, 200)
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
                "status": "active"
            }},
            status=200
        )

    def test_patch_to_cancelled(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "cancelled",
                "cancellation": {
                    "description": "text"
                }
            }}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "cancelled")

    def test_patch_to_cancelled_with_no_report(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "cancelled"
            }}, status=422
        )
        self.assertEqual(('body', 'cancellation'), next(get_errors_field_names(response, 'This field is required.')))

    def test_fail_change_status_not_exists(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "closed",
            }},
            status=422
        )
        self.assertEqual(
            response.json["errors"],
            [{
                'description': 'Status update from "draft" to "closed" is not allowed.',
                'location': 'body',
                'name': 'status'
            }]
        )

    test_masking_monitoring = masking_monitoring


class ActiveMonitoringResourceTest(BaseWebTest):
    def setUp(self):
        super(ActiveMonitoringResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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

    def test_patch_add_conclusion_with_no_violations(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": False,
                }
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["violationOccurred"], False)

    def test_patch_add_conclusion_with_violations(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "conclusion": {
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType"],
                },
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["conclusion"]["violationOccurred"], True)
        self.assertEqual(response.json['data']["conclusion"]["violationType"], ["corruptionProcurementMethodType"])

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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "declined")

    def test_patch_to_declined_with_no_conclusion(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "declined",
            }}, status=422
        )

        self.assertEqual(('body', 'conclusion'), next(get_errors_field_names(response, 'This field is required.')))

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

        self.assertEqual(response.status_code, 403)
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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "addressed")

    def test_patch_to_addressed_with_no_conclusion(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "addressed",
            }}, status=422
        )

        self.assertEqual(('body', 'conclusion'), next(get_errors_field_names(response, 'This field is required.')))

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

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content_type, 'application/json')

    def test_patch_to_stopped(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "stopped",
                "cancellation": {
                    "description": "Whisper words of wisdom - let it be."
                }
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "stopped")
        self.assertIn('cancellation', response.json['data'])

        # activate one more time
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "active",
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        # try to stop monitoring second time
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "stopped",
            }},
            status=403,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
        response.json["errors"],
            [{
                'description': "Forbidden to change status from active to stopped more than once.",
                'location': 'body',
                'name': 'status'
            }]
        )

    def test_patch_to_stopped_with_no_report(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "stopped"
            }}, status=422
        )
        self.assertEqual(('body', 'cancellation'), next(get_errors_field_names(response, 'This field is required.')))

    test_masking_monitoring = masking_monitoring


@freeze_time('2018-01-01T12:00:00.000000+03:00')
class AddressedMonitoringResourceTest(BaseWebTest):
    def setUp(self):
        super(AddressedMonitoringResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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
                    "description": "Some text",
                    "violationOccurred": True,
                    "violationType": ["corruptionProcurementMethodType", "corruptionAwarded"],
                },
                "status": "addressed",
            }},
        )

    def test_patch_add_cancellation(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "cancellation": {
                    "description": "Whisper words of wisdom - let it be."
                }
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["cancellation"]["description"], "Whisper words of wisdom - let it be.")

    def test_patch_to_stopped(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "stopped",
                "cancellation": {
                    "description": "Whisper words of wisdom - let it be."
                }
            }},
            status=422,
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json["errors"],
            [{
                'description': "Status update from \"addressed\" to \"stopped\" is not allowed.",
                'location': 'body',
                'name': 'status'
            }]
        )

    test_masking_monitoring = masking_monitoring


@freeze_time('2018-01-01T12:00:00.000000+03:00')
class DeclinedMonitoringResourceTest(BaseWebTest):
    def setUp(self):
        super(DeclinedMonitoringResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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

    @freeze_time('2018-01-20T12:00:00.000000+03:00')
    def test_patch_to_closed(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "closed",
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "closed")
        self.assertIn("endDate", response.json['data'])

    def test_fail_change_status(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "closed",
            }},
            status=403
        )
        self.assertEqual(
            response.json["errors"],
            [{
                'description': "Can't change status to closed before elimination period ends.",
                'location': 'body',
                'name': 'data'
            }]
        )

    def test_patch_add_cancellation(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "cancellation": {
                    "description": "Whisper words of wisdom - let it be."
                }
            }},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["cancellation"]["description"], "Whisper words of wisdom - let it be.")

    def test_patch_to_stopped(self):
        response = self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "status": "stopped",
                "cancellation": {
                    "description": "Whisper words of wisdom - let it be."
                }
            }},
            status=422,
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json["errors"],
            [{
                'description': "Status update from \"declined\" to \"stopped\" is not allowed.",
                'location': 'body',
                'name': 'status'
            }]
        )

    test_masking_monitoring = masking_monitoring


@freeze_time('2025-10-29T12:00:00.000000+03:00')
class StoppedMonitoringResourceTest(BaseWebTest):
    def setUp(self):
        super(StoppedMonitoringResourceTest, self).setUp()
        self.create_monitoring()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
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
        self.monitoring_period = response.json["data"]["monitoringPeriod"]

    @parameterized.expand([
        ('2025-10-31T12:00:00+02:00', '2025-11-04T10:00:00+02:00', '2025-11-22T00:00:00+02:00'),
        ('2025-11-20T12:00:00+02:00', '2025-11-25T17:00:00+02:00', '2025-11-20T00:00:00+02:00'),
        ('2025-11-25T12:00:00+02:00', '2025-11-27T18:00:00+02:00', '2025-11-20T00:00:00+02:00'),
        ('2025-10-29T12:00:00+02:00', '2025-10-31T11:00:00+02:00', '2025-11-22T00:00:00+02:00'),
        ('2025-10-30T12:00:00+02:00', '2025-10-31T15:00:00+02:00', '2025-11-21T00:00:00+02:00'),
        ('2025-11-05T12:00:00+02:00', '2025-11-11T10:00:00+02:00', '2025-11-26T00:00:00+02:00'),
    ])
    @unittest.skipIf(SANDBOX_MODE, "Skip test with accelerator")
    def test_patch_to_active(self, cancellation_date, activation_date, monitoring_period_end_date):
        with freeze_time(cancellation_date):
            response = self.app.patch_json(
                '/monitorings/{}'.format(self.monitoring_id),
                {"data": {
                    "status": "stopped",
                    "cancellation": {
                        "description": "Whisper words of wisdom - let it be."
                    }
                }},
            )
            self.assertEqual(response.json["data"]["status"], "stopped")

        with freeze_time(activation_date):
            response = self.app.patch_json(
                '/monitorings/{}'.format(self.monitoring_id),
                {"data": {
                    "status": "active",
                }},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")
        self.assertEqual(response.json['data']["monitoringPeriod"]["startDate"], self.monitoring_period["startDate"])
        self.assertEqual(response.json['data']["monitoringPeriod"]["endDate"], monitoring_period_end_date)
