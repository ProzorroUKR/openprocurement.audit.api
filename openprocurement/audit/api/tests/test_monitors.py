from openprocurement.audit.api.tests.base import BaseWebTest
from math import ceil
import unittest

from openprocurement.audit.api.tests.utils import get_errors_field_names


class MonitoringsEmptyListingResourceTest(BaseWebTest):

    def test_get(self):
        response = self.app.get('/monitorings')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_post_monitoring_without_authorisation(self):
        self.app.post_json('/monitorings', {}, status=403)

    def test_post_monitoring_broker(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        self.app.post_json('/monitorings', {}, status=403)

    def test_post_monitoring_sas_empty_body(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitorings', {}, status=422)
        self.assertEqual(
            {('body', 'data')},
            get_errors_field_names(response, "Data not available"))

    def test_post_monitoring_sas_empty_data(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitorings', {"data": {}}, status=422)
        self.assertEqual(
            {('body', "reasons"), ('body', "tender_id"), ('body', "procuringStages")},
            get_errors_field_names(response, 'This field is required.'))

    def test_post_monitoring_sas(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitorings',
            {"data": {
                "tender_id": "f" * 32,
                "reasons": ["public", "fiscal"],
                "procuringStages": ["awarding", "contracting"]
            }},
            status=201
        )

        self.assertIn("data", response.json)
        self.assertEqual(
            set(response.json["data"]),
            {"id", "status", "tender_id", "dateModified",
             "dateCreated", "reasons", "monitoring_id", "procuringStages"}
        )
        self.assertEqual(response.json["data"]["status"], "draft")


class BaseFeedResourceTest(BaseWebTest):
    feed = ""
    status = ""
    limit = 3
    fields = ""
    expected_fields = {"id", "dateModified"}
    descending = ""

    def setUp(self):
        super(BaseFeedResourceTest, self).setUp()

        self.expected_ids = []
        for i in range(19):
            monitoring = self.create_monitoring()
            self.expected_ids.append(monitoring["id"])

    def test_pagination(self):
        # go through the feed forward
        url = '/monitorings?limit={}&feed={}&opt_fields={}&descending={}&status={}'.format(
            self.limit, self.feed, self.fields, self.descending, self.status
        )
        offset = 0
        pages = int(ceil(len(self.expected_ids) / float(self.limit)))
        for i in range(pages + 2):
            response = self.app.get(url)
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertIn("data", response.json)

            if i < pages:
                self.assertEqual(self.expected_fields, set(response.json['data'][0]))
                self.assertEqual([m["id"] for m in response.json['data']],
                                 self.expected_ids[offset:offset + self.limit])
                offset += self.limit

            else:
                self.assertEqual(response.json['data'], [])

            self.assertIn("next_page", response.json)
            url = response.json["next_page"]["path"]
        # go back
        for _ in range(pages):
            self.assertIn("prev_page", response.json)
            response = self.app.get(response.json["prev_page"]["path"])
            self.assertEqual(self.expected_fields, set(response.json['data'][0]))
            offset -= self.limit
            self.assertEqual([m["id"] for m in response.json['data']],
                             self.expected_ids[offset:offset + self.limit])

        self.assertNotIn("prev_page", response.json)


class DescendingFeedResourceTest(BaseFeedResourceTest):
    limit = 2
    descending = "anything"

    def setUp(self):
        super(DescendingFeedResourceTest, self).setUp()
        self.expected_ids = list(reversed(self.expected_ids))


class ChangesFeedResourceTest(BaseFeedResourceTest):
    limit = 4
    feed = "changes"


class ChangesDescFeedResourceTest(BaseFeedResourceTest):
    limit = 1
    feed = "changes"
    descending = True

    def setUp(self):
        super(ChangesDescFeedResourceTest, self).setUp()
        self.expected_ids = list(reversed(self.expected_ids))


class StatusFeedResourceTest(BaseFeedResourceTest):
    status = "active"

    expected_fields = {"id", "dateModified", "tender_id"}
    fields = ",".join(expected_fields)

    def setUp(self):
        super(StatusFeedResourceTest, self).setUp()

        self.expected_ids = []
        for i in range(13):
            monitoring = self.create_monitoring(status="active")
            self.expected_ids.append(monitoring["id"])


class StatusFeedCustomFieldsResourceTest(BaseFeedResourceTest):
    limit = 10
    status = "active"
    expected_fields = {"id", "dateCreated", "dateModified", "tender_id"}
    fields = ",".join(expected_fields)

    def setUp(self):
        super(StatusFeedCustomFieldsResourceTest, self).setUp()

        self.expected_ids = []
        for i in range(13):
            monitoring = self.create_monitoring(status="active")
            self.expected_ids.append(monitoring["id"])


class StatusDescFeedResourceTest(BaseFeedResourceTest):
    status = "draft"
    descending = True

    def setUp(self):
        super(StatusDescFeedResourceTest, self).setUp()
        self.expected_ids = list(reversed(self.expected_ids))

        for i in range(13):
            self.create_monitoring(status="active")


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitoringsEmptyListingResourceTest))
    s.addTest(unittest.makeSuite(BaseFeedResourceTest))
    s.addTest(unittest.makeSuite(DescendingFeedResourceTest))
    s.addTest(unittest.makeSuite(ChangesFeedResourceTest))
    s.addTest(unittest.makeSuite(ChangesDescFeedResourceTest))
    s.addTest(unittest.makeSuite(StatusFeedResourceTest))
    s.addTest(unittest.makeSuite(StatusDescFeedResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')