from math import ceil
from unittest import mock

from openprocurement.audit.api.constants import CANCELLED_STATUS, ACTIVE_STATUS
from openprocurement.audit.monitoring.tests.base import BaseWebTest, DSWebTestMixin
from openprocurement.audit.monitoring.tests.utils import get_errors_field_names


class MonitoringsEmptyListingResourceTest(BaseWebTest, DSWebTestMixin):

    def setUp(self):
        super(MonitoringsEmptyListingResourceTest, self).setUp()
        self.app.app.registry.docservice_url = 'http://localhost'

    def test_get(self):
        response = self.app.get('/monitorings')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], [])

    def test_post_monitoring_without_authorisation(self):
        self.app.post_json('/monitorings', {}, status=403)

    def test_post_monitoring_broker(self):
        self.app.authorization = ('Basic', (self.broker_name, self.broker_pass))
        self.app.post_json('/monitorings', {}, status=403)

    def test_post_monitoring_sas_empty_body(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/monitorings', {}, status=422)
        self.assertEqual(
            ('body', 'data'),
            next(get_errors_field_names(response, "Data not available")))

    def test_post_monitoring_sas_empty_data(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        response = self.app.post_json('/monitorings', {"data": {}}, status=422)
        self.assertEqual(
            {
                ('body', "reasons"),
                ('body', "tender_id"),
                ('body', "procuringStages")
            },
            set(get_errors_field_names(response, 'This field is required.')))

    def test_post_monitoring_sas(self):

        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))

        with mock.patch('openprocurement.audit.monitoring.utils.TendersClient') as mock_api_client:
            mock_api_client.return_value.get_tender.return_value = {'config': {'restricted': False}}
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
             "dateCreated", "reasons", "monitoring_id", "procuringStages", "restricted", "owner"}
        )
        self.assertEqual(response.json["data"]["status"], "draft")

    def test_post_monitoring_risk_bot(self):
        self.app.authorization = ('Basic', (self.risk_indicator_name, self.risk_indicator_pass))
        data = {
            "tender_id": "f" * 32,
            "reasons": ["public", "fiscal"],
            "procuringStages": ["awarding", "contracting"],
            "riskIndicators": ['some_risk_indicator_id', 'some_other_id'],
            "riskIndicatorsTotalImpact": 1.099999,
            "riskIndicatorsRegion": u"Севастополь",
            "decision": {
                "description": "some text 123",
                "documents": [
                    {
                        'title': 'lorem.doc',
                        'url': self.generate_docservice_url(),
                        'hash': 'md5:' + '0' * 32,
                        'format': 'application/msword',
                    },
                ]
            }
        }
        with mock.patch('openprocurement.audit.monitoring.utils.TendersClient') as mock_api_client:
            mock_api_client.return_value.get_tender.return_value = {'config': {'restricted': False}}
            response = self.app.post_json(
                '/monitorings',
                {"data": data},
                status=201
            )

        self.assertIn("data", response.json)
        self.assertEqual(
            set(response.json["data"]),
            {"id", "status", "tender_id", "dateModified", "dateCreated", "reasons", "monitoring_id",
             "procuringStages", "riskIndicators", "riskIndicatorsTotalImpact", "riskIndicatorsRegion", "restricted", "owner"}
        )
        self.assertEqual(response.json["data"]["status"], "draft")

        obj = self.app.app.registry.mongodb.monitoring.get(response.json["data"]["id"])
        self.assertEqual(obj["decision"]["description"], data["decision"]["description"])
        self.assertEqual(obj["decision"]['documents'][0]['title'], data["decision"]['documents'][0]['title'])
        self.assertNotEqual(obj["decision"]['documents'][0]['url'], data["decision"]['documents'][0]['url'])
        self.assertIn("author", obj["decision"]['documents'][0])

    def test_post_active_monitoring_risk_bot(self):
        self.app.authorization = ('Basic', (self.risk_indicator_name, self.risk_indicator_pass))
        response = self.app.post_json(
            '/monitorings',
            {"data": {
                "tender_id": "f" * 32,
                "reasons": ["public", "fiscal"],
                "procuringStages": ["awarding", "contracting"],
                "status": "active",
            }},
            status=422
        )
        self.assertEqual(response.json["errors"][0]["description"], "Can't create a monitoring in 'active' status.")

    def test_post_not_allowed_fields(self):
        self.app.authorization = ('Basic', (self.risk_indicator_name, self.risk_indicator_pass))
        with mock.patch('openprocurement.audit.monitoring.utils.TendersClient') as mock_api_client:
            mock_api_client.return_value.get_tender.return_value = {'config': {'restricted': False}}
            response = self.app.post_json(
                '/monitorings',
                {"data": {
                    "tender_id": "f" * 32,
                    "reasons": ["public", "fiscal"],
                    "procuringStages": ["awarding", "contracting"],
                    "status": "draft",
                    "eliminationReport": {
                        "description": "Report from the tender owner"
                    }
                }},
            )
            self.assertNotIn("eliminationReport", response.json["data"])


class BaseFeedResourceTest(BaseWebTest):
    feed = ""
    limit = 3
    fields = ""
    expected_fields = {"id", "dateModified"}
    descending = ""

    def setUp(self):
        super(BaseFeedResourceTest, self).setUp()

        self.expected_ids = []
        for i in range(19):
            monitoring = self.create_active_monitoring()
            self.expected_ids.append(monitoring["id"])

    def test_pagination(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        # go through the feed forward
        url = '/monitorings?limit={}&feed={}&opt_fields={}&descending={}'.format(
            self.limit, self.feed, self.fields, self.descending,
        )
        offset = 0
        pages = int(ceil(len(self.expected_ids) / float(self.limit)))
        for i in range(pages + 2):
            response = self.app.get(url)
            self.assertEqual(response.status_code, 200)
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

    def test_opt_fields(self):
        response = self.app.get("/monitorings?opt_fields=reasons,status,procuringStages,conclusion")
        self.assertIn("reasons", response.json["data"][0])
        self.assertIn("status", response.json["data"][0])
        self.assertIn("procuringStages", response.json["data"][0])
        self.assertNotIn("conclusion", response.json["data"][0])


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


class DraftChangesFeedTestCase(BaseWebTest):

    def setUp(self):
        super(DraftChangesFeedTestCase, self).setUp()

        self.expected_test_ids = []
        self.expected_real_ids = []

        for test_mode in range(2):
            for i in range(2):
                if test_mode:
                    self.create_monitoring(mode="test")
                    self.expected_test_ids.append(self.monitoring_id)

                else:
                    self.create_monitoring()
                    self.expected_real_ids.append(self.monitoring_id)

                if i % 2 == 0:
                    self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
                    self.app.patch_json(
                        '/monitorings/{}'.format(self.monitoring_id),
                        {'data': {
                            "status": CANCELLED_STATUS,
                            'cancellation': {
                                'description': 'some_description'
                            }
                        }})

    def test_real_draft_forbidden(self):
        self.app.authorization = None
        url = '/monitorings?mode=real_draft&feed=changes'
        response = self.app.get(url, status=403)
        self.assertEqual(
            response.json,
            {u'status': u'error', u'errors': [
                {u'description': u'Forbidden', u'location': u'url', u'name': u'permission'}]})

    def test_all_draft_forbidden(self):
        self.app.authorization = None
        url = '/monitorings?mode=all_draft&feed=changes'
        response = self.app.get(url, status=403)
        self.assertEqual(
            response.json,
            {u'status': u'error', u'errors': [
                {u'description': u'Forbidden', u'location': u'url', u'name': u'permission'}]})

    def test_real_draft(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        url = '/monitorings?mode=real_draft&feed=changes'
        response = self.app.get(url)
        self.assertEqual(len(response.json["data"]), 2)
        self.assertEqual(set(e["id"] for e in response.json["data"]), set(self.expected_real_ids))

    def test_all_draft(self):
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        url = '/monitorings?mode=all_draft&feed=changes'
        response = self.app.get(url)
        self.assertEqual(len(response.json["data"]), 4)
        self.assertEqual(set(e["id"] for e in response.json["data"]),
                         set(self.expected_real_ids + self.expected_test_ids))


class FeedVisibilityTestCase(BaseWebTest):

    def setUp(self):
        super(FeedVisibilityTestCase, self).setUp()
        self.app.authorization = ('Basic', (self.sas_name, self.sas_pass))
        # real
        self.create_monitoring()
        self.draft_id = self.monitoring_id

        self.create_monitoring()
        self.cancelled_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description'
                }
            }})

        self.create_monitoring()
        self.active_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {"description": "text"},
                "status": ACTIVE_STATUS,
            }}
        )
        # test
        self.create_monitoring(mode="test")
        self.test_draft_id = self.monitoring_id

        self.create_monitoring(mode="test")
        self.test_cancelled_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {'data': {
                "status": CANCELLED_STATUS,
                'cancellation': {
                    'description': 'some_description'
                }
            }})

        self.create_monitoring(mode="test")
        self.test_active_id = self.monitoring_id
        self.app.patch_json(
            '/monitorings/{}'.format(self.monitoring_id),
            {"data": {
                "decision": {"description": "text"},
                "status": ACTIVE_STATUS,
            }}
        )

    # dateModified
    def test_real_date_modified(self):
        url = '/monitorings'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id}
        )

        url = '/monitorings?feed=dateModified'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id}
        )

    def test_test_date_modified(self):
        url = '/monitorings?mode=test'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.test_active_id}
        )

        url = '/monitorings?feed=dateModified&mode=test'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.test_active_id}
        )

    def test_all_date_modified(self):
        url = '/monitorings?mode=_all_'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.test_active_id}
        )

        url = '/monitorings?feed=dateModified&mode=_all_'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.test_active_id}
        )

    def test_real_draft_date_modified(self):
        url = '/monitorings?mode=real_draft'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.draft_id, self.cancelled_id}
        )

        url = '/monitorings?feed=dateModified&mode=real_draft'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.draft_id, self.cancelled_id}
        )

    def test_all_draft_date_modified(self):
        url = '/monitorings?mode=all_draft'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.draft_id, self.cancelled_id,
             self.test_active_id, self.test_draft_id, self.test_cancelled_id}
        )

        url = '/monitorings?feed=dateModified&mode=all_draft'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.draft_id, self.cancelled_id,
             self.test_active_id, self.test_draft_id, self.test_cancelled_id}
        )

    # changes
    def test_real_changes(self):
        url = '/monitorings?feed=changes'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id}
        )

    def test_test_changes(self):
        url = '/monitorings?feed=changes&mode=test'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.test_active_id}
        )

    def test_all_changes(self):
        url = '/monitorings?feed=changes&mode=_all_'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.test_active_id}
        )

    def test_real_draft_changes(self):
        url = '/monitorings?feed=changes&mode=real_draft'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.draft_id, self.cancelled_id}
        )

    def test_all_draft_changes(self):
        url = '/monitorings?feed=changes&mode=all_draft'
        response = self.app.get(url)
        self.assertEqual(
            set(e["id"] for e in response.json["data"]),
            {self.active_id, self.draft_id, self.cancelled_id,
             self.test_active_id, self.test_draft_id, self.test_cancelled_id}
        )
