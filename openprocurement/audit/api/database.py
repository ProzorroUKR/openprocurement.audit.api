# -*- coding: utf-8 -*-
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.collection import ReturnDocument
from uuid import uuid4


DATABASE = None


def init_db(mongodb_uri, db_name):
    global DATABASE
    connection = MongoClient(mongodb_uri)
    DATABASE = getattr(connection, db_name)
    return DATABASE


def get_database():
    return DATABASE


def get_sequences_collection():
    return DATABASE.sequences


def get_next_sequence_value(uid):
    collection = get_sequences_collection()
    result = collection.find_one_and_update(
        {'_id': uid},
        {"$inc": {"value": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )
    return result["value"]


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


def save_data(collection, data, insert=False):
    uid_field = "id" if "id" in data else "_id"
    uid = data.pop(uid_field)
    filters = {'_id': uid}
    if not insert:
        # get current revision to filters, so you only save successfully
        # if the _rev hasn't changed since you fetched the object
        filters["_rev"] = data.pop("_rev")

    data["_rev"] = get_next_rev(filters.get("_rev"))
    res = collection.find_one_and_update(
        filters,
        {"$set": data},
        return_document=ReturnDocument.AFTER,
        upsert=insert
    )
    return res


def rename_id(obj):
    if obj:
        obj["id"] = obj.pop("_id")
    return obj


def list_items(
        collection,
        filters=None,
        projection=None,
        offset="",
        limit=1000,
        descending=False,
        mode=None,
        offset_field="dateModified",
        **_
):
    limit = min(limit, 1000)
    filters = filters or {}
    if mode != "all":
        filters["mode"] = {"$eq" if mode == "test" else "$ne": "test"}
    if offset:
        filters[offset_field] = {"$lt" if descending else "$gt": offset}
    if projection:
        projection.add("_id")
        projection.add(offset_field)

    items = collection.find(
        filters,
        projection=projection,
    ).sort(
        offset_field,
        DESCENDING if descending else ASCENDING
    ).limit(limit)
    items = list(items)
    return items


def append_indexes(collection, fields):
    for field in fields:
        collection.create_index([(field, ASCENDING)], background=True)
