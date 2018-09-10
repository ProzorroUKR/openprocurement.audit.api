# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition
from openprocurement.api import design


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


# the view below is used for an internal system monitoring
def monitorings_all_view(doc):
    if doc.get("doc_type") == "Monitoring":
        yield doc['dateModified'], None



def monitorings_by_dateModified_view(doc):
    if doc.get("doc_type") == "Monitoring" and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


def monitorings_real_by_dateModified_view(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


def monitorings_test_by_dateModified_view(doc):
    if doc.get("doc_type") == "Monitoring" and doc.get("mode") == "test" and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


def monitorings_real_draft_by_dateModified_view(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc:
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


def monitorings_draft_by_dateModified_view(doc):
    if doc.get("doc_type") == "Monitoring":
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


def monitorings_by_local_seq_view(doc):
    if doc.get("doc_type") == "Monitoring" and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


def monitorings_real_by_local_seq_view(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


def monitorings_test_by_local_seq_view(doc):
    if doc.get("doc_type") == "Monitoring" and doc.get("mode") == 'test' and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


def monitorings_real_draft_by_local_seq_view(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc:
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


def monitorings_draft_by_local_seq_view(doc):
    if doc.get("doc_type") == "Monitoring":
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


def monitorings_by_tender_id_view(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ("status",) if doc.get(k) is not None}
        yield (doc['tender_id'], doc['dateCreated']), data


def monitorings_test_by_tender_id_view(doc):
    if doc.get("doc_type") == "Monitoring" and doc.get("mode") == 'test' and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ("status",) if doc.get(k) is not None}
        yield (doc['tender_id'], doc['dateCreated']), data


def monitorings_draft_by_tender_id_view(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc:
        data = {k: doc[k] for k in ("status",) if doc.get(k) is not None}
        yield (doc['tender_id'], doc['dateCreated']), data


for name, obj in globals().items():
    if name.endswith("_view") and callable(obj):
        parts = name.split("_")
        globals()[name] = ViewDefinition(parts[0], "_".join(parts[1:-1]), obj, language='python')