# -*- coding: utf-8 -*-
from unittest.mock import Mock
from pyramid.testing import DummyRequest

from openprocurement.audit.api.tests.base import BaseWebTest
from openprocurement.audit.api.utils import APIResourceListing


class ItemsListing(APIResourceListing):
    def __init__(self, request, context):
        super(ItemsListing, self).__init__(request, context)

        results = (
            Mock(
                key=k,
                value={
                    "status": "active",
                    "title": "title#%d" % k,
                    "description": "description#%d" % k,
                    "bids": [1, k]
                },
                doc={
                    "id": k,
                    "dateModified": "yesterday",
                    "status": "active",
                    "title": "title#%d" % k,
                    "description": "description#%d" % k,
                    "bids": [1, k],
                    "secret": "pass",
                }
            ) for k in range(5)
        )

        self.view_mock = Mock(return_value=results)
        self.test_view_mock = Mock(return_value=results)
        self.changes_view_mock = Mock(return_value=results)
        self.test_changes_view_mock = Mock(return_value=results)
        self.VIEW_MAP = {
            u'': self.view_mock,
            u'test': self.test_view_mock,
        }
        self.CHANGES_VIEW_MAP = {
            u'': self.changes_view_mock,
            u'test': self.test_changes_view_mock,
        }
        self.FEED = {
            u'dateModified': self.VIEW_MAP,
            u'changes': self.CHANGES_VIEW_MAP,
        }
        self.FIELDS = ('id', 'status', 'title', 'description')

        def item_serialize(_, data, fields):
            return {i: j for i, j in data.items() if i in fields and i != "secret"}

        self.serialize_func = item_serialize
        self.object_name_for_listing = 'health'
        self.log_message_id = 'items_list_custom'


class ResourceListingTestCase(BaseWebTest):

    def setUp(self):
        self.request = DummyRequest()
        self.request.logging_context = {}
        self.request._registry = self.app.app.registry
        self.listing = ItemsListing(self.request, {})

    def get_listing(self):
        return self.listing.get()

    def test_get_listing(self):
        self.get_listing()
        self.listing.view_mock.assert_called_once_with(
            self.db,
            startkey='', stale='update_after', descending=False, limit=100
        )

    def test_get_test_listing(self):
        self.request.params = {"opt_fields": "id,status", "mode": "test"}
        self.get_listing()
        self.listing.test_view_mock.assert_called_once_with(
            self.db,
            startkey='', stale='update_after', descending=False, limit=100
        )

    def test_get_changes_listing(self):
        self.request.params = {"opt_fields": "id,status", "feed": "changes"}
        self.get_listing()
        self.listing.changes_view_mock.assert_called_once_with(
            self.db,
            startkey=0, stale='update_after', descending=False, limit=100
        )

    def test_get_test_changes_listing(self):
        self.request.params = {"opt_fields": "id,status", "feed": "changes", "mode": "test"}
        self.get_listing()
        self.listing.test_changes_view_mock.assert_called_once_with(
            self.db,
            startkey=0, stale='update_after', descending=False, limit=100
        )

    def test_get_listing_opt_fields_subset(self):
        self.request.params = {"opt_fields": "id,status"}
        self.get_listing()
        self.listing.view_mock.assert_called_once_with(
            self.db,
            startkey='', stale='update_after', descending=False, limit=100
        )

    def test_get_listing_opt_fields_not_subset(self):
        self.request.params = {"opt_fields": "id,status,title,description,bids"}
        data = self.get_listing()
        self.listing.view_mock.assert_called_once_with(
            self.db,
            startkey='', stale='update_after', descending=False, limit=100
        )
        self.assertEqual(len(data["data"]), 5)
        self.assertEqual(set(data["data"][0].keys()), {"id", "status", "title", "description", "dateModified"})

    def test_get_listing_opt_fields_not_subset_disable_filter(self):
        self.listing.disable_opt_fields_filter = True
        self.request.params = {"opt_fields": "id,status,title,description,bids,secret"}
        data = self.get_listing()
        self.listing.view_mock.assert_called_once_with(
            self.db, include_docs=True,
            startkey='', stale='update_after', descending=False, limit=100
        )
        self.assertEqual(len(data["data"]), 5)
        self.assertEqual(set(data["data"][0].keys()),
                         {"id", "status", "title", "description", "dateModified", "bids"})
