# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch
from pyramid.testing import DummyRequest

from openprocurement.audit.api.database import rename_id
from openprocurement.audit.api.tests.base import BaseWebTest
from openprocurement.audit.api.utils import APIResourceListing


class ResourceListingTestCase(BaseWebTest):

    def get_listing(self):
        request = DummyRequest()
        request.logging_context = {}
        request._registry = self.app.app.registry

        listing = APIResourceListing(request, {})
        listing.listing_name = 'health'

        return listing

    @patch("openprocurement.audit.api.utils."
           "APIResourceListing.db_listing_method")
    def test_get_listing(self, listing_mock):
        listing = self.get_listing()
        listing.get()

        listing_mock.assert_called_once_with(
            descending='',
            filters=None,
            limit=1000,
            mode='',
            offset='',
            offset_field='dateModified',
            projection={'dateModified', 'id'}
        )

    @patch("openprocurement.audit.api.utils."
           "APIResourceListing.db_listing_method")
    @patch("openprocurement.audit.api.utils."
           "APIResourceListing.get_listing_serialize")
    def test_listing_not_subset(self, get_serialize_mock, listing_mock):
        get_serialize_mock.return_value.return_value = {
            "id": 1,
            "status": "draft",
            "dateModified": "12",
        }
        listing_mock.return_value = [
            {"_id": 1, "status": "draft", "token": "secret", "dateModified": ""}
        ]

        listing = self.get_listing()
        listing.request.params = {"opt_fields": "id,status", "mode": "test"}
        result = listing.get()

        listing_mock.assert_called_once_with(
            descending='',
            filters=None,
            limit=1000,
            mode='test',
            offset='',
            offset_field='dateModified',
            projection=None
        )
        get_serialize_mock.assert_called_once_with()
        get_serialize_mock.return_value.assert_called_once_with(
            data=listing_mock.return_value[0],
            fields={'dateModified', 'status', 'id'},
        )
        self.assertEqual(result["data"],
                         [get_serialize_mock.return_value.return_value])

    @patch("openprocurement.audit.api.utils."
           "APIResourceListing.db_listing_method")
    @patch("openprocurement.audit.api.utils."
           "APIResourceListing.get_listing_serialize")
    def test_get_listing_opt_fields_is_subset(self, get_serialize_mock,
                                              listing_mock):
        get_serialize_mock.return_value.return_value = {
            "id": 1,
            "status": "draft",
            "dateModified": "12",
        }
        listing_return = {"_id": 1, "status": "draft",
                          "token": "secret", "dateModified": ""}
        listing_mock.return_value = [dict(**listing_return)]

        listing = self.get_listing()
        listing.request.params = {"opt_fields": "id,dateCreated",
                                  "mode": "all"}
        result = listing.get()

        listing_mock.assert_called_once_with(
            descending='',
            filters=None,
            limit=1000,
            mode='all',
            offset='',
            offset_field='dateModified',
            projection={"id", "dateCreated", "dateModified"}
        )
        get_serialize_mock.assert_not_called()
        self.assertEqual(
            result["data"],
            [rename_id(listing_return)]
        )
