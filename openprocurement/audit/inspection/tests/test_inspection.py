from freezegun import freeze_time
from openprocurement.audit.inspection.tests.base import BaseWebTest


@freeze_time('2018-01-01T11:00:00+02:00')
class InspectionResourceTest(BaseWebTest):

    def test_get_404(self):
        self.create_inspection()
        self.app.get('/inspections/{}'.format("fake_id"), status=404)

    def test_get(self):
        self.create_inspection()

        response = self.app.get('/inspections/{}'.format(self.inspection_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        data = response.json['data']
        self.assertEqual(
            set(data.keys()),
            {
                'id',
                'monitoring_ids',
                'documents',
                'description',
                'inspection_id',
                'dateCreated',
                'dateModified',
                'restricted',
            }
        )
        self.assertEqual(data["id"], self.inspection_id)

    def test_patch_forbidden(self):
        self.create_inspection()

        self.app.patch_json(
            '/inspections/{}'.format(self.inspection_id),
            {"description": "I regretted my decision"},
            status=403
        )

    def test_patch_nothing(self):
        initial_data = self.create_inspection()

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        modified_date = '2018-01-02T13:30:00+02:00'
        with freeze_time(modified_date):
            response = self.app.patch_json(
                '/inspections/{}'.format(self.inspection_id),
                {"data": {
                    "description": initial_data["description"],
                }}
            )
        self.assertNotEqual(response.json["data"]["dateModified"], modified_date)
        self.assertEqual(response.json["data"]["dateModified"], initial_data["dateModified"])

    def test_patch(self):
        self.create_inspection()

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "description": "I regretted my decision",
            "monitoring_ids": ["5" * 32, "3" * 32]
        }

        modified_date = '2018-01-02T13:30:00+02:00'
        with freeze_time(modified_date):
            response = self.app.patch_json(
                '/inspections/{}'.format(self.inspection_id),
                {"data": request_data}
            )
        self.assertEqual(response.json["data"]["monitoring_ids"], request_data["monitoring_ids"])
        self.assertEqual(response.json["data"]["description"], request_data["description"])
        self.assertEqual(response.json["data"]["dateModified"], modified_date)

    def test_patch_validation_error(self):
        self.create_inspection()

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        request_data = {
            "description": 12.5,
            "monitoring_ids": "something else"
        }
        response = self.app.patch_json(
            '/inspections/{}'.format(self.inspection_id),
            {"data": request_data},
            status=422,
        )
        self.assertEqual(
            response.json["errors"],
            [
                {
                    "location": "body",
                    "name": "monitoring_ids",
                    "description": [
                        "Hash value is wrong length."
                    ]
                },
                {
                    "location": "body",
                    "name": "description",
                    "description": [
                        "Couldn't interpret '12.5' as string."
                    ]
                },

            ]
        )
