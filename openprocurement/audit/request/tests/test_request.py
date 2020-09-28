from freezegun import freeze_time

from openprocurement.audit.request.tests.base import BaseWebTest


@freeze_time("2018-01-01T11:00:00+02:00")
class RequestResourceTest(BaseWebTest):
    def test_get_404(self):
        self.create_request()
        self.app.get("/requests/{}".format("fake_id"), status=404)

    def test_get_archive(self):
        data = self.create_request()

        doc = self.db.get(data["id"])
        doc["doc_type"] = "request"
        self.db.save(doc)

        response = self.app.get("/requests/{}".format(data["id"]), status=410)
        self.assertEqual(
            response.json["errors"],
            [{"location": "url", "name": "request_id", "description": "Archived"}],
        )

    def test_get(self):
        self.create_request()

        self.app.authorization = None
        response = self.app.get("/requests/{}".format(self.request_id))
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "documents",
                "description",
                "violationType",
                "requestId",
                "dateCreated",
                "dateModified",
                "parties",
                "tenderId"
            },
        )
        self.assertEqual(
            set(data["parties"][0].keys()),
            {
                "id",
                "name",
                "datePublished",
                "roles",
            },
        )
        self.assertEqual(data["id"], self.request_id)

    def test_get_sas(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        response = self.app.get("/requests/{}".format(self.request_id))
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "documents",
                "description",
                "violationType",
                "requestId",
                "dateCreated",
                "dateModified",
                "parties",
                "tenderId"
            },
        )
        self.assertEqual(
            set(data["parties"][0].keys()),
            {
                "id",
                "name",
                "address",
                "contactPoint",
                "datePublished",
                "roles",
            },
        )
        self.assertEqual(
            set(data["parties"][0]["address"].keys()),
            {
                "streetAddress",
                "locality",
                "region",
                "postalCode",
                "countryName",
            },
        )
        self.assertEqual(
            set(data["parties"][0]["contactPoint"].keys()),
            {
                "email",
            },
        )
        self.assertEqual(data["id"], self.request_id)

    def test_patch_forbidden(self):
        self.create_request()

        self.app.patch_json(
            "/requests/{}".format(self.request_id),
            {"description": "I regretted my decision"},
            status=403,
        )

    def test_patch_sas_public_fields(self):
        initial_data = self.create_request()

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        modified_date = "2018-01-02T13:30:00+02:00"
        with freeze_time(modified_date):
            response = self.app.patch_json(
                "/requests/{}".format(self.request_id),
                {
                    "data": {
                        "description": "Knock-knock",
                    }
                },
            )
        self.assertNotEqual(response.json["data"]["dateModified"], modified_date)
        self.assertEqual(
            response.json["data"]["dateModified"], initial_data["dateModified"]
        )

    def test_patch_sas_answer_reason_fields(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        request_data = {
            "answer": "monitoringCreated",
            "reason": "Because i am your father",
        }

        modified_date = "2018-01-02T13:30:00+02:00"
        with freeze_time(modified_date):
            response = self.app.patch_json(
                "/requests/{}".format(self.request_id), {"data": request_data}
            )
        self.assertEqual(response.json["data"]["answer"], request_data["answer"])
        self.assertEqual(response.json["data"]["dateModified"], modified_date)
        self.assertEqual(response.json["data"]["dateAnswered"], modified_date)

    def test_patch_sas_answer_twice_forbidden(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        request_data = {
            "answer": "monitoringCreated",
            "reason": "Because i am your father",
        }

        response = self.app.patch_json(
            "/requests/{}".format(self.request_id), {"data": request_data}
        )
        response = self.app.patch_json(
            "/requests/{}".format(self.request_id), {"data": request_data}, status=403
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_validation_error(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        request_data = {"answer": 12.5}
        response = self.app.patch_json(
            "/requests/{}".format(self.request_id),
            {"data": request_data},
            status=422,
        )
        self.assertEqual(
            response.json["errors"],
            [
                {
                    "location": "body",
                    "name": "answer",
                    "description": ["Couldn't interpret '12.5' as string."],
                },
            ],
        )
