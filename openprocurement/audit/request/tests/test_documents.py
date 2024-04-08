from freezegun import freeze_time

from openprocurement.audit.request.tests.base import BaseWebTest


@freeze_time("2018-01-01T11:00:00+02:00")
class RequestDocumentsResourceTest(BaseWebTest):
    def test_get_list(self):
        self.create_request()
        response = self.app.get(
            "/requests/{}/documents".format(
                self.request_id,
            )
        )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(
            set(data[0].keys()),
            {
                "id",
                "hash",
                "url",
                "datePublished",
                "dateModified",
                "title",
                "format",
                "author",
            },
        )
        self.assertEqual(data[0]["id"], self.document_id)

    def test_get(self):
        data = self.create_request()
        response = self.app.get(
            "/requests/{}/documents/{}".format(
                self.request_id, data["documents"][0]["id"]
            )
        )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "hash",
                "url",
                "datePublished",
                "dateModified",
                "title",
                "format",
                "previousVersions",
                "author",
            },
        )
        self.assertEqual(data["id"], self.document_id)
        self.assertEqual(data["previousVersions"], [])

    def test_get_download(self):
        data = self.create_request()
        response = self.app.get(
            "/requests/{}/documents/{}?download=1".format(
                self.request_id,
                data["documents"][0]["id"],
                status=302,
            )
        )
        self.assertIn("Content-Disposition", response.headers)
        self.assertIn("Location", response.headers)

    def test_post_no_auth_forbidden(self):
        self.create_request()
        self.app.post_json(
            "/requests/{}/documents".format(self.request_id),
            {
                "data": {
                    "title": "doc.txt",
                    "url": self.generate_docservice_url(),
                    "hash": "md5:" + "0" * 32,
                    "format": "plain/text",
                }
            },
            status=403,
        )

    def test_post_public_answered_forbidden(self):
        self.create_request()
        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        response = self.app.patch_json(
            "/requests/{}".format(self.request_id),
            {
                "data": {
                    "answer":  "monitoringCreated",
                    "reason": "Because i am your father"
                }
            }
        )
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        self.app.post_json(
            "/requests/{}/documents".format(self.request_id),
            {
                "data": {
                    "title": "doc.txt",
                    "url": self.generate_docservice_url(),
                    "hash": "md5:" + "0" * 32,
                    "format": "plain/text",
                }
            },
            status=403,
        )

    def test_post(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))

        post_time = "2018-01-02T11:30:00+02:00"
        with freeze_time(post_time):
            response = self.app.post_json(
                "/requests/{}/documents".format(self.request_id),
                {
                    "data": {
                        "title": "doc.txt",
                        "url": self.generate_docservice_url(),
                        "hash": "md5:" + "0" * 32,
                        "format": "plain/text",
                    }
                },
            )
        self.assertEqual(response.status, "201 Created")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "hash",
                "url",
                "datePublished",
                "dateModified",
                "title",
                "format",
                "author",
            },
        )
        self.assertNotEqual(data["id"], self.document_id)
        self.assertNotEqual(data["datePublished"], post_time)
        self.assertEqual(data["dateModified"], post_time)

        response = self.app.get("/requests/{}".format(self.request_id))
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.json["data"]["dateModified"], post_time)

    def test_put_forbidden(self):
        self.create_request()
        self.app.put_json(
            "/requests/{}/documents/{}".format(self.request_id, self.document_id),
            {
                "data": {
                    "title": "doc.txt",
                    "url": self.generate_docservice_url(),
                    "hash": "md5:" + "0" * 32,
                    "format": "plain/text",
                }
            },
            status=403,
        )

    def test_put(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))

        post_time = "2018-01-02T11:30:00+02:00"
        with freeze_time(post_time):
            response = self.app.put_json(
                "/requests/{}/documents/{}".format(self.request_id, self.document_id),
                {
                    "data": {
                        "title": "doc.txt",
                        "url": self.generate_docservice_url(),
                        "hash": "md5:" + "0" * 32,
                        "format": "plain/text",
                    }
                },
            )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "hash",
                "url",
                "datePublished",
                "dateModified",
                "title",
                "format",
                "author",
            },
        )
        self.assertEqual(data["id"], self.document_id)

        response = self.app.get("/requests/{}".format(self.request_id))
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.json["data"]["dateModified"], post_time)

    def test_patch_forbidden(self):
        self.create_request()
        self.app.patch_json(
            "/requests/{}/documents/{}".format(self.request_id, self.document_id),
            {
                "data": {
                    "title": "doc.txt",
                    "url": self.generate_docservice_url(),
                    "hash": "md5:" + "0" * 32,
                    "format": "plain/text",
                }
            },
            status=403,
        )

    def test_patch(self):
        self.create_request()

        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        post_time = "2018-01-02T11:30:00+02:00"
        with freeze_time(post_time):
            response = self.app.patch_json(
                "/requests/{}/documents/{}".format(self.request_id, self.document_id),
                {
                    "data": {
                        "title": "doc.txt",
                        "url": self.generate_docservice_url(),
                        "hash": "md5:" + "0" * 32,
                        "format": "plain/text",
                    }
                },
            )
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        data = response.json["data"]
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "hash",
                "url",
                "datePublished",
                "dateModified",
                "title",
                "format",
                "author",
            },
        )
        self.assertEqual(data["id"], self.document_id)

        response = self.app.get("/requests/{}".format(self.request_id))
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.json["data"]["dateModified"], post_time)
