from openprocurement.audit.api.tests.base import BaseWebTest
from math import ceil
import unittest


class MonitorsEmptyListingResourceTest(BaseWebTest):

    def test_get(self):
        response = self.app.get('/monitors')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_post_monitor_without_authorisation(self):
        self.app.post_json('/monitors', {}, status=403)

    def test_post_monitor_broker(self):
        self.app.authorization = ('Basic', (self.broker_token, ''))
        self.app.post_json('/monitors', {}, status=403)

    def test_post_monitor_sas_empty_body(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitors', {}, status=422)
        self.assertEqual(len(response.json.get("errors", [])), 1)
        self.assertEqual(response.json["errors"][0]["description"], "Data not available")

    def test_post_monitor_sas_empty_data(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json('/monitors', {"data": {}}, status=422)
        self.assertEqual(set(e["name"] for e in response.json["errors"]), {"reasons", "tender_id", "procuringStages"})

    def test_post_monitor_sas(self):
        self.app.authorization = ('Basic', (self.sas_token, ''))
        response = self.app.post_json(
            '/monitors',
            {"data": {
                "tender_id": "f" * 32,
                "reasons": ["public", "fiscal"],
                "procuringStages": ["awarding", "contracting"]
            }},
            status=201
        )

        self.assertIn("access", response.json)
        self.assertIn("token", response.json["access"])

        self.assertIn("data", response.json)
        self.assertEqual(
            set(response.json["data"]),
            {"id", "status", "tender_id", "owner", "dateModified",
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
            monitor = self.create_monitor()
            self.expected_ids.append(monitor["id"])

    def test_pagination(self):
        # go through the feed forward
        url = '/monitors?limit={}&feed={}&opt_fields={}&descending={}&status={}'.format(
            self.limit, self.feed, self.fields, self.descending, self.status
        )
        offset = 0
        pages = int(ceil(len(self.expected_ids) / float(self.limit)))
        for i in range(pages):
            response = self.app.get(url)
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertIn("data", response.json)
            self.assertEqual(self.expected_fields, set(response.json['data'][0]))
            self.assertEqual([m["id"] for m in response.json['data']],
                             self.expected_ids[offset:offset + self.limit])

            if i < pages - 1:
                self.assertIn("next_page", response.json)
                url = response.json["next_page"]["path"]
                offset += self.limit

        # go back
        for _ in range(pages - 1):
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
            monitor = self.create_monitor(status="active")
            self.expected_ids.append(monitor["id"])


class StatusFeedCustomFieldsResourceTest(BaseFeedResourceTest):
    limit = 10
    status = "active"
    expected_fields = {"id", "dateCreated", "dateModified", "tender_id"}
    fields = ",".join(expected_fields)

    def setUp(self):
        super(StatusFeedCustomFieldsResourceTest, self).setUp()

        self.expected_ids = []
        for i in range(13):
            monitor = self.create_monitor(status="active")
            self.expected_ids.append(monitor["id"])


class StatusDescFeedResourceTest(BaseFeedResourceTest):
    status = "draft"
    descending = True

    def setUp(self):
        super(StatusDescFeedResourceTest, self).setUp()
        self.expected_ids = list(reversed(self.expected_ids))

        for i in range(13):
            self.create_monitor(status="active")


def suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(MonitorsEmptyListingResourceTest))
    s.addTest(unittest.makeSuite(BaseFeedResourceTest))
    s.addTest(unittest.makeSuite(DescendingFeedResourceTest))
    s.addTest(unittest.makeSuite(ChangesFeedResourceTest))
    s.addTest(unittest.makeSuite(ChangesDescFeedResourceTest))
    s.addTest(unittest.makeSuite(StatusFeedResourceTest))
    s.addTest(unittest.makeSuite(StatusDescFeedResourceTest))
    return s


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
