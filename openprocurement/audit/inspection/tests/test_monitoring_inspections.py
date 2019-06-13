from freezegun import freeze_time

from openprocurement.audit.inspection.tests.base import BaseWebTest


@freeze_time('2018-01-01T11:00:00+02:00')
class MonitoringInspectionsResourceTest(BaseWebTest):

    def test_get_empty(self):
        response = self.app.get('/monitorings/{}/inspections'.format("f" * 32))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get(self):
        self.create_inspection()

        for uid in self.monitoring_ids:
            response = self.app.get('/monitorings/{}/inspections'.format(uid))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data'],
                [{
                    u'dateCreated': u'2018-01-01T11:00:00+02:00',
                    u'dateModified': u'2018-01-01T11:00:00+02:00',
                    u'inspection_id': self.inspectionId,
                    u'id': self.inspection_id
                }]
            )

    def test_get_opt_fields(self):
        self.create_inspection()

        for uid in self.monitoring_ids:
            response = self.app.get('/monitorings/{}/inspections?opt_fields=description'.format(uid))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data'],
                [{
                    u'description': u'Yo-ho-ho',
                    u'dateCreated': u'2018-01-01T11:00:00+02:00',
                    u'dateModified': u'2018-01-01T11:00:00+02:00',
                    u'inspection_id': self.inspectionId,
                    u'id': self.inspection_id
                }]
            )

    def test_get_two(self):
        self.create_inspection()
        expected_one = {
            u'dateCreated': u'2018-01-01T11:00:00+02:00',
            u'dateModified': u'2018-01-01T11:00:00+02:00',
            u'inspection_id': self.inspectionId,
            u'id': self.inspection_id
        }

        with freeze_time('2018-01-01T11:00:50+02:00'):
            self.create_inspection()

        expected_two = {
            u'dateCreated': u'2018-01-01T11:00:50+02:00',
            u'dateModified': u'2018-01-01T11:00:50+02:00',
            u'inspection_id': self.inspectionId,
            u'id': self.inspection_id
        }

        for uid in self.monitoring_ids:
            response = self.app.get('/monitorings/{}/inspections'.format(uid))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data'],
                [expected_one, expected_two]
            )
