from openprocurement.audit.api.database import BaseCollection
from pymongo import IndexModel, ASCENDING
import logging


logger = logging.getLogger(__name__)


class RequestCollection(BaseCollection):
    object_name = "request"

    def get_indexes(self):
        # Making multiple indexes with the same unique key is supposed to be impossible
        # https://jira.mongodb.org/browse/SERVER-25023
        # and https://docs.mongodb.com/manual/core/index-partial/#restrictions
        # ``In MongoDB, you cannot create multiple versions of an index that differ only in the options.
        #   As such, you cannot create multiple partial indexes that differ only by the filter expression.``
        # Hold my 🍺
        test_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("existing_key", ASCENDING)],
            name="test_by_public_modified",
            partialFilterExpression={
                "is_test": True,
            },
        )
        real_by_public_modified = IndexModel(
            [("public_modified", ASCENDING)],
            name="real_by_public_modified",
            partialFilterExpression={
                "is_test": False,
            },
        )
        all_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("surely_existing_key", ASCENDING)],  # makes key unique https://jira.mongodb.org/browse/SERVER-25023
            name="all_by_public_modified",
        )
        # answered / not answered
        real_is_answered_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("answered_string_existing_key", ASCENDING)],
            name="real_is_answered_by_public_modified",
            partialFilterExpression={
                "is_test": False,
                "is_answered": True,
            },
        )
        real_not_is_answered_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("real_is_answered_by_public_modified", ASCENDING)],  # makes key unique https://jira.mongodb.org/browse/SERVER-25023
            name="real_not_is_answered_by_public_modified",
            partialFilterExpression={
                "is_test": False,
                "is_answered": False,
            },
        )
        all_by_tender_id = IndexModel(
            [("tender_id", ASCENDING),
             ("dateCreated", ASCENDING)],
            name="all_by_tender_id_created",
        )
        all_indexes = [
            test_by_public_modified,
            real_by_public_modified,
            all_by_public_modified,
            real_is_answered_by_public_modified,
            real_not_is_answered_by_public_modified,
            all_by_tender_id,
        ]
        return all_indexes

    # because of partialFilterExpression we're limited in filter conditions
    # https://www.mongodb.com/docs/manual/core/index-partial/#create-a-partial-index
    # so I have to add is_answered boolean field for store use only
    def save(self, o, insert=False, modified=True):
        data = o.to_primitive()

        data["is_answered"] = "answer" in data  # <- this added

        updated = self.store.save_data(self.collection, data, insert=insert, modified=modified)
        o.import_data(updated)

    def get(self, uid):
        doc = super().get(uid)
        if isinstance(doc, dict):
            doc.pop("is_answered", None)
        return doc
