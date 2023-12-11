import os
from uuid import uuid4
from logging import getLogger
from pymongo import MongoClient, ReturnDocument, DESCENDING, ASCENDING, ReadPreference, IndexModel
from pymongo.write_concern import WriteConcern
from pymongo.read_concern import ReadConcern
from bson.codec_options import TypeRegistry, TypeCodec, CodecOptions
from bson.decimal128 import Decimal128
from decimal import Decimal
from openprocurement.audit.api.context import get_now, get_db_session, get_request
from pprint import pprint
from bson.raw_bson import RawBSONDocument


LOGGER = getLogger("{}.init".format(__name__))


def print_cursor_explain(cursor):
    def to_native(data):
        if isinstance(data, dict):
            data = {k: to_native(v) for k, v in data.items()}
        elif isinstance(data, list):
            data = [to_native(v) for v in data]
        elif isinstance(data, RawBSONDocument):
            data = {k: to_native(v) for k, v in data.items()}
        return data

    explain_data = cursor.explain()
    pprint(
        to_native(explain_data)
    )


#  mongodb
class MongodbResourceConflict(Exception):
    """
    On doc update we pass _id and _rev as filter
    _rev can be changed by concurrent requests
    then update_one(or replace_one) doesn't find any document to update and returns matched_count = 0
    that causes MongodbResourceConflict that is shown to the User as 409 response code
    that means they have to retry his request
    """


class DecimalCodec(TypeCodec):
    python_type = Decimal    # the Python type acted upon by this type codec
    bson_type = Decimal128   # the BSON type acted upon by this type codec

    def transform_python(self, value):
        """Function that transforms a custom type value into a type
        that BSON can encode."""
        return Decimal128(value)

    def transform_bson(self, value):
        """Function that transforms a vanilla BSON type value into our
        custom type."""
        return value.to_decimal()


type_registry = TypeRegistry([
    DecimalCodec(),
])
codec_options = CodecOptions(type_registry=type_registry)
COLLECTION_CLASSES = {}


def get_public_modified():
    public_modified = {"$divide": [{"$toLong": "$$NOW"}, 1000]}
    return public_modified


class MongodbStore:

    def __init__(self, settings):
        db_name = os.environ.get("DB_NAME", settings["mongodb.db_name"])
        mongodb_uri = os.environ.get("MONGODB_URI", settings["mongodb.uri"])
        max_pool_size = int(os.environ.get("MONGODB_MAX_POOL_SIZE", settings["mongodb.max_pool_size"]))
        min_pool_size = int(os.environ.get("MONGODB_MIN_POOL_SIZE", settings["mongodb.min_pool_size"]))

        # https://docs.mongodb.com/manual/core/causal-consistency-read-write-concerns/#causal-consistency-and-read-and-write-concerns
        raw_read_preference = os.environ.get(
            "READ_PREFERENCE",
            settings.get("mongodb.read_preference", "SECONDARY_PREFERRED")
        )
        raw_w_concert = os.environ.get(
            "WRITE_CONCERN",
            settings.get("mongodb.write_concern", "majority")
        )
        raw_r_concern = os.environ.get(
            "READ_CONCERN",
            settings.get("mongodb.read_concern", "majority")
        )
        self.connection = MongoClient(
            mongodb_uri,
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
        )
        self.database = self.connection.get_database(
            db_name,
            read_preference=getattr(ReadPreference, raw_read_preference),
            write_concern=WriteConcern(w=int(raw_w_concert) if raw_w_concert.isnumeric() else raw_w_concert),
            read_concern=ReadConcern(level=raw_r_concern),
            codec_options=codec_options,
        )

        # code related to specific packages, like:
        # store.plans.get(uid) or store.tenders.save(doc) or store.tenders.count(filters)
        for name, cls in COLLECTION_CLASSES.items():
            setattr(self, name, cls(self, settings))

    def get_sequences_collection(self):
        return self.database.sequences

    def get_next_sequence_value(self, uid):
        collection = self.get_sequences_collection()
        result = collection.find_one_and_update(
            {'_id': uid},
            {"$inc": {"value": 1}},
            return_document=ReturnDocument.AFTER,
            upsert=True,
            session=get_db_session(),
        )
        return result["value"]

    def flush_sequences(self):
        collection = self.get_sequences_collection()
        self.flush(collection)

    @staticmethod
    def get_next_rev(current_rev=None):
        """
        This mimics couchdb _rev field
        that prevents concurrent updates
        :param current_rev:
        :return:
        """
        if current_rev:
            version, _ = current_rev.split("-")
            version = int(version)
        else:
            version = 1
        next_rev = f"{version + 1}-{uuid4().hex}"
        return next_rev

    @staticmethod
    def get(collection, uid):
        res = collection.find_one(
            {'_id': uid},
            projection={"is_public": False, "is_test": False},
            session=get_db_session(),
        )
        return res

    def list(self, collection, fields, offset_field="_id", offset_value=None, descending=False, limit=0, filters=None):
        filters = filters or {}
        if offset_value:
            filters[offset_field] = {"$lt" if descending else "$gt": offset_value}
        results = list(collection.find(
            filter=filters,
            projection={f: 1 for f in fields | {offset_field}},
            limit=limit,
            sort=((offset_field, DESCENDING if descending else ASCENDING),),
            session=get_db_session(),
        ))
        for e in results:
            self.rename_id(e)
        return results

    def save_data(self, collection, data, insert=False, modified=True):
        uid = data.pop("id" if "id" in data else "_id")
        revision = data.pop("rev" if "rev" in data else "_rev", None)

        data['_id'] = uid
        data["_rev"] = self.get_next_rev(revision)
        data["is_test"] = data.get("mode") == "test"
        if "is_masked" in data and data.get("is_masked") is not True:
            data.pop("is_masked")

        pipeline = [
            {"$replaceWith": {"$literal": data}},
        ]
        if insert:
            data["dateCreated"] = get_now().isoformat()
        if modified:
            data["dateModified"] = get_now().isoformat()
            pipeline.append(
                {"$set": {
                    "public_modified": get_public_modified()
                }}
            )
        result = collection.find_one_and_update(
            {
                "_id": uid,
                "_rev": revision
            },
            pipeline,
            upsert=insert,
            session=get_db_session(),
        )
        if not result:
            if insert:
                pass  # it's fine, when upsert=True works and document is created it's not returned by default
            else:
                raise MongodbResourceConflict("Conflict while updating document. Please, retry")
        return data

    @staticmethod
    def flush(collection):
        result = collection.delete_many({})
        return result

    @staticmethod
    def delete(collection, uid):
        result = collection.delete_one({"_id": uid}, session=get_db_session())
        return result

    @staticmethod
    def rename_id(obj):
        if obj:
            obj["id"] = obj.pop("_id")
        return obj


class BaseCollection:

    object_name = "dummy"

    def __init__(self, store, settings):
        self.store = store
        collection_name = os.environ.get(f"{self.object_name.upper()}_COLLECTION",
                                         settings[f"mongodb.{self.object_name.lower()}_collection"])
        self.collection = getattr(store.database, collection_name)
        if isinstance(self.collection.read_preference, type(ReadPreference.PRIMARY)):
            self.collection_primary = self.collection
        else:
            self.collection_primary = self.collection.with_options(read_preference=ReadPreference.PRIMARY)
        self.create_indexes()

    def get_indexes(self):
        return []

    def create_indexes(self):
        indexes = self.get_indexes()
        self.collection.drop_indexes()
        # index management probably shouldn't be a part of api initialization
        # a command like `migrate_db` could be called once per release
        # that can manage indexes and data migrations
        # for now I leave it here
        if indexes:
            self.collection.create_indexes(indexes)

    def save(self, o, insert=False, modified=True):
        data = o.to_primitive()
        updated = self.store.save_data(self.collection, data, insert=insert, modified=modified)
        o.import_data(updated)

    def get(self, uid):
        # if a client doesn't use SESSION cookie
        # reading from primary solves the issues
        # when write operation is allowed because of a state object from a secondary replica
        # This means more reads from Primary, but at the moment we can't force everybody to use the cookie
        collection = (
            self.collection
            if getattr(get_request(), "method", None) in ("GET", "HEAD")
            else self.collection_primary
        )
        doc = self.store.get(collection, uid)
        return doc

    def list(self, **kwargs):
        result = self.store.list(self.collection, **kwargs)
        return result

    def flush(self):
        self.store.flush(self.collection)

    def delete(self, uid):
        result = self.store.delete(self.collection, uid)
        return result

    def paging_list(
        self, skip=0, limit=1000, fields=None, sort_by="dateCreated", descending=False, filters=None,
    ):
        filters = filters or {}
        result = list(self.collection.find(
            filter=filters,
            projection=fields if fields else None,
            sort=((sort_by, DESCENDING if descending else ASCENDING),),
            skip=skip,
            limit=limit,
            session=get_db_session(),
        ))

        count = self.collection.count_documents(
            filter=filters,
            session=get_db_session(),
        )
        return result, count
