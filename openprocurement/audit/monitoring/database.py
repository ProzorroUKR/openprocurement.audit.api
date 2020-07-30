# -*- coding: utf-8 -*-
from openprocurement.audit.api.database import (
    get_database,
    append_indexes,
    save_data,
    list_items,
)


# Monitoring
def get_monitoring_collection():
    return get_database().monitorings


def add_monitoring_indexes():
    collection = get_monitoring_collection()
    fields = ("status", "mode", "tender_id", "dateModified")
    append_indexes(collection, fields)


def get_monitoring(uid):
    result = get_monitoring_collection().find_one({"_id": uid})
    return result


def list_monitoring(*_, **kwargs):
    passed_mode = kwargs.pop("mode")
    # default mode for monitoring is "real & non-drafts"
    if "test" in passed_mode:
        kwargs["mode"] = "test"
    elif "all" in passed_mode:
        kwargs["mode"] = "all"
    else:
        kwargs["mode"] = ""

    if "draft" not in passed_mode:
        # filter out cancelled and drafts
        kwargs["filters"] = {"status": {"$nin": ("draft", "cancelled")}}

    collection = get_monitoring_collection()
    return list_items(collection, **kwargs)


def save_monitoring(data, insert=False):
    collection = get_monitoring_collection()
    return save_data(collection, data, insert=insert)


def count_monitoring(mode=""):
    collection = get_monitoring_collection()
    filters = {}
    if mode != "all":
        filters["mode"] = {"$eq" if mode else "$ne": "test"}
    count = collection.find(filters).count()
    return count


