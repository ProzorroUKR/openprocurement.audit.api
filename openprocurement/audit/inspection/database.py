# -*- coding: utf-8 -*-
from openprocurement.audit.api.database import (
    get_database,
    append_indexes,
    save_data,
    list_items,
)


def get_inspection_collection():
    return get_database().inspections


def add_inspection_indexes():
    collection = get_inspection_collection()
    fields = ("mode", "monitoring_ids", "dateModified")
    append_indexes(collection, fields)


def get_inspection(uid):
    result = get_inspection_collection().find_one({"_id": uid})
    return result


def save_inspection(data, insert=False):
    collection = get_inspection_collection()
    return save_data(collection, data, insert=insert)


def list_inspections(*args, **kwargs):
    collection = get_inspection_collection()
    return list_items(collection, **kwargs)
