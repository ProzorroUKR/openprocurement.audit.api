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
                [{
                    u'dateCreated': u'2018-01-01T11:00:00+02:00',
                    u'dateModified': u'2018-01-01T11:00:00+02:00',
                    u'inspection_id': self.inspectionId,
                    u'id': self.inspection_id
                }],
                response.json['data'],
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

    def test_restricted_visibility(self):
        self.create_inspection(restricted_config=True)

        for uid in self.monitoring_ids:
            self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
            response = self.app.get(f'/monitorings/{uid}/inspections?opt_fields=description')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data'],
                [{
                    'description': 'Приховано',
                    'dateCreated': '2018-01-01T11:00:00+02:00',
                    'dateModified': '2018-01-01T11:00:00+02:00',
                    'inspection_id': self.inspectionId,
                    'id': self.inspection_id
                }]
            )
            self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
            response = self.app.get(f'/monitorings/{uid}/inspections?opt_fields=description')
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['data'][0]['description'], 'Yo-ho-ho')

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

    def test_get_with_pagination(self):
        for i in range(5):
            self.create_inspection()

        for uid in self.monitoring_ids:
            response = self.app.get(
                '/monitorings/{}/inspections?limit=2&page=2'.format(uid)
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['total'], 5)
            self.assertEqual(response.json['count'], 2)
            self.assertEqual(response.json['limit'], 2)
            self.assertEqual(response.json['page'], 2)
            self.assertEqual(len(response.json['data']), 2)

    def test_get_with_pagination_not_full_page(self):
        for i in range(5):
            self.create_inspection()

        for uid in self.monitoring_ids:
            response = self.app.get(
                '/monitorings/{}/inspections?limit=2&page=3'.format(uid)
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['total'], 5)
            self.assertEqual(response.json['count'], 1)
            self.assertEqual(response.json['limit'], 2)
            self.assertEqual(response.json['page'], 3)
            self.assertEqual(len(response.json['data']), 1)

    def test_get_with_pagination_out_of_bounds_page(self):
        for i in range(5):
            self.create_inspection()

        for uid in self.monitoring_ids:
            response = self.app.get(
                '/monitorings/{}/inspections?limit=2&page=4'.format(uid)
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['total'], 5)
            self.assertEqual(response.json['count'], 0)
            self.assertEqual(response.json['limit'], 2)
            self.assertEqual(response.json['page'], 4)
            self.assertEqual(len(response.json['data']), 0)
