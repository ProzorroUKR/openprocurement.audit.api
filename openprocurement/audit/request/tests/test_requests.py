from freezegun import freeze_time

from openprocurement.audit.api.choices import VIOLATION_TYPE_CHOICES
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names
from openprocurement.audit.request.tests.base import BaseWebTest


@freeze_time("2018-01-01T11:00:00+02:00")
class RequestsListingResourceTest(BaseWebTest):
    def test_get_empty(self):
        response = self.app.get("/requests")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(response.json["data"], [])

    def test_get(self):
        self.create_request()

        response = self.app.get("/requests")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(
            response.json["data"],
            [{u"dateModified": u"2018-01-01T11:00:00+02:00", u"id": self.request_id}],
        )

    def test_get_modes(self):
        for i in range(5):
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

        response = self.app.get("/requests")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(len(response.json["data"]), 5)

        response = self.app.get("/requests?mode=answered")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(len(response.json["data"]), 1)

        response = self.app.get("/requests?mode=not_answered")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(len(response.json["data"]), 4)

        response = self.app.get("/requests?feed=changes")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(len(response.json["data"]), 5)

        response = self.app.get("/requests?feed=changes&mode=answered")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(len(response.json["data"]), 1)

        response = self.app.get("/requests?feed=changes&mode=not_answered")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(len(response.json["data"]), 4)

    def test_get_opt_fields(self):
        self.create_request()

        response = self.app.get("/requests?opt_fields=requestId")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(
            response.json["data"],
            [
                {
                    u"dateModified": u"2018-01-01T11:00:00+02:00",
                    u"requestId": u"UA-R-2018-01-01-000001",
                    u"id": self.request_id,
                }
            ],
        )

    def test_post_request_without_authorisation(self):
        self.app.post_json("/requests", {}, status=403)

    def test_post_request_broker(self):
        self.app.authorization = ("Basic", (self.broker_name, self.broker_pass))
        self.app.post_json("/requests", {}, status=403)

    def test_post_request_sas(self):
        self.app.authorization = ("Basic", (self.sas_name, self.sas_pass))
        self.app.post_json("/requests", {}, status=403)

    def test_post_request_public_empty_body(self):
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        response = self.app.post_json("/requests", {}, status=422)
        self.assertEqual(
            {("body", "data")},
            set(get_errors_field_names(response, "Data not available")),
        )

    def test_post_request_public_empty_data(self):
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        response = self.app.post_json("/requests", {"data": {}}, status=422)
        self.assertEqual(
            {
                ("body", "description"),
                ("body", "violationType"),
                ("body", "parties"),
                ("body", "tenderId"),
                ("body", "documents"),
            },
            set(get_errors_field_names(response, "This field is required.")),
        )

    def test_post_request_public_empty_party_data(self):
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        response = self.app.post_json(
            "/requests",
            {
                "data": {
                    "tenderId": "f" * 32,
                    "description": "Yo-ho-ho",
                    "violationType": VIOLATION_TYPE_CHOICES,
                    "parties": [{}],
                    "documents": [
                        {
                            "title": "doc.txt",
                            "url": self.generate_docservice_url(),
                            "hash": "md5:" + "0" * 32,
                            "format": "plain/text",
                        },
                    ],
                }
            },
            status=422,
        )
        self.assertEqual(
            {
                ("body", "parties", "name"),
                ("body", "parties", "address"),
                ("body", "parties", "contactPoint"),
            },
            set(get_errors_field_names(response, "This field is required.")),
        )

    def test_post_request_public_empty_address_data(self):
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        response = self.app.post_json(
            "/requests",
            {
                "data": {
                    "tenderId": "f" * 32,
                    "description": "Yo-ho-ho",
                    "violationType": VIOLATION_TYPE_CHOICES,
                    "parties": [{
                        "name": "party name",
                        "address": {},
                        "contactPoint": {
                            "email": "test@example.com"
                        }
                    }],
                    "documents": [
                        {
                            "title": "doc.txt",
                            "url": self.generate_docservice_url(),
                            "hash": "md5:" + "0" * 32,
                            "format": "plain/text",
                        },
                    ],
                }
            },
            status=422,
        )
        self.assertEqual(
            {
                ("body", "parties", "address", "streetAddress"),
                ("body", "parties", "address", "locality"),
                ("body", "parties", "address", "region"),
                ("body", "parties", "address", "postalCode"),
                ("body", "parties", "address", "countryName"),
            },
            set(get_errors_field_names(response, "This field is required.")),
        )

    def test_post_request_public_empty_contact_point_data(self):
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        response = self.app.post_json(
            "/requests",
            {
                "data": {
                    "tenderId": "f" * 32,
                    "description": "Yo-ho-ho",
                    "violationType": VIOLATION_TYPE_CHOICES,
                    "parties": [{
                        "name": "party name",
                        "address": {
                            "streetAddress": "test street address",
                            "locality": "test locality",
                            "region": "test region",
                            "postalCode": "test postalCode",
                            "countryName": "test country",
                        },
                        "contactPoint": {}
                    }],
                    "documents": [
                        {
                            "title": "doc.txt",
                            "url": self.generate_docservice_url(),
                            "hash": "md5:" + "0" * 32,
                            "format": "plain/text",
                        },
                    ],
                }
            },
            status=422,
        )
        self.assertEqual(
            {
                ("body", "parties", "contactPoint", "email"),
            },
            set(get_errors_field_names(response, "This field is required.")),
        )

    def test_post_request_public(self):
        self.app.authorization = ("Basic", (self.public_name, self.public_pass))
        document_url = self.generate_docservice_url()
        response = self.app.post_json(
            "/requests",
            {
                "data": {
                    "tenderId": "f" * 32,
                    "description": "Yo-ho-ho",
                    "violationType": VIOLATION_TYPE_CHOICES,
                    "parties": [
                        {
                            "name": "party name",
                            "address": {
                                "streetAddress": "test street address",
                                "locality": "test locality",
                                "region": "test region",
                                "postalCode": "test postalCode",
                                "countryName": "test country",
                            },
                            "contactPoint": {
                                "email": "test@example.com"
                            }
                        }
                    ],
                    "documents": [
                        {
                            "title": "doc.txt",
                            "url": document_url,
                            "hash": "md5:" + "0" * 32,
                            "format": "plain/text",
                        },
                    ],
                }
            },
            status=201,
        )

        self.assertIn("data", response.json)
        self.assertNotEqual(document_url, response.json["data"]["documents"][0]["url"])
        self.assertEqual(
            set(response.json["data"]),
            {
                "id",
                "requestId",
                "dateModified",
                "dateCreated",
                "description",
                "violationType",
                "parties",
                "tenderId",
                "documents",
                "owner",
            },
        )
        self.assertIn("Location", response.headers)
