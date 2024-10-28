from unittest import mock

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
        with mock.patch(
                'openprocurement.audit.inspection.views.inspection.extract_restricted_config_from_monitoring'
        ) as mock_get_monitoring:
            mock_get_monitoring.return_value = False
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
             "dateCreated", "monitoring_ids", "description", "restricted", "owner"}
        )
        self.assertIn("Location", response.headers)
        inspection_id = response.json["data"]["id"]

        # check fields not masking for restricted=False monitoring
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/inspections/{inspection_id}')
        self.assertEqual(response.json["data"]["description"], "Yo-ho-ho")

        response = self.app.get(f'/inspections?opt_fields=description')
        self.assertEqual(response.json["data"][0]["description"], "Yo-ho-ho")

    def test_restricted_visibility(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        with mock.patch(
                'openprocurement.audit.inspection.views.inspection.extract_restricted_config_from_monitoring'
        ) as mock_get_monitoring:
            mock_get_monitoring.return_value = True
            response = self.app.post_json(
                '/inspections',
                {"data": {
                    "monitoring_ids": ["f" * 32],
                    "description": "Yo-ho-ho",
                    "documents": [{
                        "title": "doc.txt",
                        "url": self.generate_docservice_url(),
                        "hash": "md5:" + '0' * 32,
                        "format": "plain/text",
                    }],
                }},
                status=201
            )
            inspection_id = response.json["data"]["id"]

        response = self.app.get(f'/inspections/{inspection_id}')
        self.assertEqual(response.json["data"]["description"], "Yo-ho-ho")
        self.assertEqual(response.json["data"]["documents"][0]["title"], "doc.txt")
        self.assertIn("http://localhost", response.json['data']["documents"][0]["url"])

        response = self.app.get(f'/inspections?opt_fields=description,documents')
        self.assertEqual(response.json["data"][0]["description"], "Yo-ho-ho")
        self.assertEqual(response.json["data"][0]["documents"][0]["title"], "doc.txt")
        self.assertIn("http://localhost", response.json['data'][0]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name_r, self.broker_pass_r))
        response = self.app.get(f'/inspections/{inspection_id}')
        self.assertEqual(response.json["data"]["description"], "Yo-ho-ho")
        self.assertEqual(response.json["data"]["documents"][0]["title"], "doc.txt")
        self.assertIn("http://localhost", response.json['data']["documents"][0]["url"])

        response = self.app.get(f'/inspections?opt_fields=description,documents')
        self.assertEqual(response.json["data"][0]["description"], "Yo-ho-ho")
        self.assertEqual(response.json["data"][0]["documents"][0]["title"], "doc.txt")
        self.assertIn("http://localhost", response.json['data'][0]["documents"][0]["url"])

        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        response = self.app.get(f'/inspections/{inspection_id}')
        self.assertEqual(response.json["data"]["description"], "Приховано")
        self.assertEqual(response.json["data"]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data']["documents"][0]["url"], "Приховано")

        response = self.app.get(f'/inspections?opt_fields=description,documents')
        self.assertEqual(response.json["data"][0]["description"], "Приховано")
        self.assertEqual(response.json["data"][0]["documents"][0]["title"], "Приховано")
        self.assertEqual(response.json['data'][0]["documents"][0]["url"], "Приховано")
