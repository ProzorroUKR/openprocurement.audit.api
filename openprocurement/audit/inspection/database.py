from openprocurement.audit.api.database import BaseCollection
from pymongo import ASCENDING, IndexModel
import logging


logger = logging.getLogger(__name__)


class InspectionCollection(BaseCollection):
    object_name = "inspection"

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
            name="ins_test_by_public_modified",
            partialFilterExpression={
                "is_test": True,
            },
        )
        real_by_public_modified = IndexModel(
            [("public_modified", ASCENDING)],
            name="ins_real_by_public_modified",
            partialFilterExpression={
                "is_test": False,
            },
        )
        all_by_public_modified = IndexModel(
            [("public_modified", ASCENDING),
             ("surely_existing_key", ASCENDING)],
            name="ins_all_by_public_modified",
        )
        all_by_monitoring_ids = IndexModel(
            [("monitoring_ids", ASCENDING),
             ("dateCreated", ASCENDING)],
            name="ins_all_by_monitoring_ids",
        )
        all_indexes = [
            test_by_public_modified,
            real_by_public_modified,
            all_by_public_modified,
            all_by_monitoring_ids,
        ]
        return all_indexes
