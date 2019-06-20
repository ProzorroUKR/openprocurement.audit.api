import unittest

from freezegun import freeze_time

from openprocurement.audit.monitoring.tests.utils import get_errors_field_names
from openprocurement.audit.inspection.tests.base import BaseWebTest


@freeze_time('2018-01-01T11:00:00+02:00')
class InspectionsListingResourceTest(BaseWebTest):

    def test_get_empty(self):
        response = self.app.get('/inspections')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_get(self):
        self.create_inspection()

        response = self.app.get('/inspections')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data'],
            [{u'dateModified': u'2018-01-01T11:00:00+02:00', u'id': self.inspection_id}]
        )

    def test_get_opt_fields(self):
        self.create_inspection()

        response = self.app.get('/inspections?opt_fields=inspection_id')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data'],
            [{u'dateModified': u'2018-01-01T11:00:00+02:00',
              u'inspection_id': u'UA-I-2018-01-01-000001',
              u'id': self.inspection_id}]
        )

    def test_post_inspection_without_authorisation(self):
        self.app.post_json('/inspections', {}, status=403)

    def test_post_inspection_broker(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.post_json('/inspections', {}, status=403)

    def test_post_inspection_sas_empty_body(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/inspections', {}, status=422)
        self.assertEqual(
            {('body', 'data')},
            set(get_errors_field_names(response, "Data not available")))

    def test_post_inspection_sas_empty_data(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/inspections', {"data": {}}, status=422)
        self.assertEqual(
            {('body', "monitoring_ids"),
             ('body', "description")},
            set(get_errors_field_names(response, 'This field is required.'))
        )

    def test_post_inspection_sas(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json(
            '/inspections',
            {"data": {
                "monitoring_ids": ["f" * 32, "e" * 32, "d" * 32],
                "description": "Yo-ho-ho"
            }},
            status=201
        )

        self.assertIn("data", response.json)
        self.assertEqual(
            set(response.json["data"]),
            {"id", "inspection_id", "dateModified",
             "dateCreated", "monitoring_ids", "description"}
        )
        self.assertIn("Location", response.headers)


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(InspectionsListingResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
