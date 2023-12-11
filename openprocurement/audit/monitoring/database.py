from openprocurement.audit.api.database import BaseCollection
from openprocurement.audit.api.context import get_db_session
from pymongo import DESCENDING, ASCENDING, IndexModel
import logging


logger = logging.getLogger(__name__)


class MonitoringCollection(BaseCollection):
    object_name = "monitoring"

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
                "is_public": True,
            },
        )
        real_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("real_surely_existing_key", ASCENDING)],
            name="real_by_public_modified",
            partialFilterExpression={
                "is_test": False,
                "is_public": True,
            },
        )
        all_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("surely_existing_key", ASCENDING)],  # makes key unique https://jira.mongodb.org/browse/SERVER-25023
            name="all_by_public_modified",
            partialFilterExpression={
                "is_public": True,
            },
        )
        # with drafts
        real_with_drafts_by_public_modified = IndexModel(
            [("public_modified", ASCENDING)],
            name="real_draft_by_public_modified",
            partialFilterExpression={
                "is_test": False,
            },
        )
        all_with_drafts_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("surely_draft_existing_key", ASCENDING)],  # makes key unique https://jira.mongodb.org/browse/SERVER-25023
            name="all_draft_by_public_modified",
        )
        all_by_tender_id = IndexModel(
            [("tender_id", ASCENDING),
             ("dateCreated", ASCENDING)],  # makes key unique https://jira.mongodb.org/browse/SERVER-25023
            name="all_by_tender_id_created",
        )
        all_indexes = [
            test_by_public_modified,
            real_by_public_modified,
            all_by_public_modified,
            real_with_drafts_by_public_modified,
            all_with_drafts_by_public_modified,
            all_by_tender_id,
        ]
        return all_indexes

    def save(self, o, insert=False, modified=True):
        data = o.to_primitive()

        data["is_public"] = data.get("status") not in ("draft", "cancelled")

        updated = self.store.save_data(self.collection, data, insert=insert, modified=modified)
        o.import_data(updated)

    def count(self, mode=""):
        filters = {}
        if mode == "test":
            filters["is_test"] = True
        elif "all" not in mode:
            filters["is_test"] = False
        count = self.collection.count_documents(
            filter=filters,
            session=get_db_session(),
        )
        return count

