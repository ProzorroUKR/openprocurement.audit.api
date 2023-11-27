import unittest

from openprocurement.audit.api.constants import CANCELLED_STATUS, ACTIVE_STATUS
from openprocurement.audit.monitoring.tests.base import BaseWebTest


class TenderMonitoringsResourceTest(BaseWebTest):

    def test_get_empty_list(self):
        response = self.app.get('/tenders/f9f9f9/monitorings')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get(self):
        tender_id = "f" * 32

        ids = []
        for i in range(10):
            self.create_monitoring(tender_id=tender_id)
            ids.append(self.monitoring_id)

        for i in range(5):  # these are not on the list
            self.create_monitoring(tender_id="a" * 32)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get('/tenders/{}/monitorings?mode=draft'.format(tender_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual([e["id"] for e in response.json['data']], ids)
        self.assertEqual(set(response.json['data'][0].keys()),
                         {"id", "dateCreated", "dateModified", "status"})

    def test_get_without_draft(self):
        tender_id = "f" * 32
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.create_monitoring(tender_id=tender_id)
        draft_id = self.monitoring_id

        self.create_monitoring(tender_id=tender_id)
        cancelled_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description'
                }
            }})

        self.create_monitoring(tender_id=tender_id)
        active_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {"description": "text"},
                "status": ACTIVE_STATUS,
            }}
        )

        response = self.app.get('/tenders/{}/monitorings'.format(tender_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual([e["id"] for e in response.json['data']], [active_id])
        self.assertEqual(set(response.json['data'][0].keys()),
                         {"id", "dateCreated", "dateModified", "status"})

    def test_get_with_draft(self):
        tender_id = "f" * 32
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        self.create_monitoring(tender_id=tender_id)
        draft_id = self.monitoring_id

        self.create_monitoring(tender_id=tender_id)
        cancelled_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description'
                }
            }})

        self.create_monitoring(tender_id=tender_id)
        active_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {"description": "text"},
                "status": ACTIVE_STATUS,
            }}
        )

        response = self.app.get('/tenders/{}/monitorings?mode=draft'.format(tender_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual({e["id"] for e in response.json['data']}, {active_id, draft_id, cancelled_id})
        self.assertEqual(set(response.json['data'][0].keys()),
                         {"id", "dateCreated", "dateModified", "status"})

    def test_get_with_draft_forbidden(self):
        tender_id = "f" * 32
        self.app.authorization = None
        response = self.app.get('/tenders/{}/monitorings?mode=draft'.format(tender_id), status=403)
        self.assertEqual(
            response.json,
            {u'status': u'error',
             u'errors': [{u'description': u'Forbidden', u'location': u'url', u'name': u'permission'}]}
        )

    def test_get_custom_fields(self):
        tender_id = "a" * 32

        ids = []
        for i in range(10):
            self.create_monitoring(tender_id=tender_id)
            ids.append(self.monitoring_id)

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.get(
            '/tenders/{}/monitorings?mode=draft&opt_fields=dateModified%2Creasons'.format(
                tender_id
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        self.assertEqual([e["id"] for e in response.json['data']], ids)
        self.assertEqual(set(response.json['data'][0].keys()),
                         {"id", "dateCreated", "dateModified", "status", "reasons"})

    def test_get_test_empty(self):
        tender_id = "a" * 32
        for i in range(10):
            self.create_monitoring(tender_id=tender_id, mode="test")

        response = self.app.get(
            '/tenders/{}/monitorings'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get_with_pagination(self):
        tender_id = "a" * 32
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        for i in range(5):
            self.create_monitoring(tender_id=tender_id)
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {"description": "text"},
                "status": ACTIVE_STATUS,
            }}
        )

        response = self.app.get(
            '/tenders/{}/monitorings?mode=draft&limit=2&page=2'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['total'], 5)
        self.assertEqual(response.json['count'], 2)
        self.assertEqual(response.json['limit'], 2)
        self.assertEqual(response.json['page'], 2)
        self.assertEqual(len(response.json['data']), 2)

    def test_get_with_pagination_not_full_page(self):
        tender_id = "a" * 32
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        for i in range(5):
            self.create_monitoring(tender_id=tender_id)

        response = self.app.get(
            '/tenders/{}/monitorings?mode=draft&limit=2&page=3'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['total'], 5)
        self.assertEqual(response.json['count'], 1)
        self.assertEqual(response.json['limit'], 2)
        self.assertEqual(response.json['page'], 3)
        self.assertEqual(len(response.json['data']), 1)

    def test_get_with_pagination_out_of_bounds_page(self):
        tender_id = "a" * 32
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        for i in range(5):
            self.create_monitoring(tender_id=tender_id)

        response = self.app.get(
            '/tenders/{}/monitorings?mode=draft&limit=2&page=4'.format(tender_id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['total'], 5)
        self.assertEqual(response.json['count'], 0)
        self.assertEqual(response.json['limit'], 2)
        self.assertEqual(response.json['page'], 4)
        self.assertEqual(len(response.json['data']), 0)
