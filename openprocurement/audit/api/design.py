# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition
from openprocurement.api import design


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


# the view below is used for an internal system monitoring
def monitoring_all(doc):
    if doc.get("doc_type") == "Monitoring":
        yield doc['dateModified'], None


monitorings_all_view = ViewDefinition('monitorings', 'all', monitoring_all, language='python')


def monitoring_by_date_modified(doc):
    if doc.get("doc_type") == "Monitoring" and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


monitorings_by_dateModified_view = ViewDefinition(
    'monitorings', 'by_dateModified', monitoring_by_date_modified, language='python')


def monitoring_real_by_date_modified(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


monitorings_real_by_dateModified_view = ViewDefinition(
    'monitorings', 'real_by_dateModified', monitoring_real_by_date_modified, language='python')


def monitoring_mode_by_date_modified(doc):
    if doc.get("doc_type") == "Monitoring" and doc.get("mode") == "test" and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


monitorings_test_by_dateModified_view = ViewDefinition(
    'monitorings', 'test_by_dateModified', monitoring_mode_by_date_modified, language='python')


def monitoring_real_draft_by_date_modified(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc:
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


monitorings_real_draft_by_dateModified_view = ViewDefinition(
    'monitorings', 'real_draft_by_dateModified', monitoring_real_draft_by_date_modified, language='python')


def monitoring_all_draft_by_date_modified(doc):
    if doc.get("doc_type") == "Monitoring":
        data = {k: doc[k] for k in ('tender_id',) if doc.get(k) is not None}
        yield doc['dateModified'], data


monitorings_all_draft_by_dateModified_view = ViewDefinition(
    'monitorings', 'draft_by_dateModified', monitoring_all_draft_by_date_modified, language='python')


def monitoring_by_local_seq(doc):
    if doc.get("doc_type") == "Monitoring" and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


monitorings_by_local_seq_view = ViewDefinition(
    'monitorings', 'by_local_seq', monitoring_by_local_seq, language='python')


def monitoring_real_by_local_seq(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


monitorings_real_by_local_seq_view = ViewDefinition(
    'monitorings', 'real_by_local_seq', monitoring_real_by_local_seq, language='python')


def monitoring_mode_by_local_seq(doc):
    if doc.get("doc_type") == "Monitoring" and doc.get("mode") == 'test' and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


monitorings_test_by_local_seq_view = ViewDefinition(
    'monitorings', 'test_by_local_seq', monitoring_mode_by_local_seq, language='python')


def monitoring_real_draft_by_local_seq(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc:
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


monitorings_real_draft_by_local_seq_view = ViewDefinition(
    'monitorings', 'real_draft_by_local_seq', monitoring_real_draft_by_local_seq, language='python')


def monitoring_all_draft_by_local_seq(doc):
    if doc.get("doc_type") == "Monitoring":
        data = {k: doc[k] for k in ('tender_id', 'dateModified') if doc.get(k) is not None}
        yield doc['_local_seq'], data


monitorings_all_draft_by_local_seq_view = ViewDefinition(
    'monitorings', 'draft_by_local_seq', monitoring_all_draft_by_local_seq, language='python')


def monitoring_by_tender_id(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ("status",) if doc.get(k) is not None}
        yield (doc['tender_id'], doc['dateCreated']), data


monitorings_by_tender_id_view = ViewDefinition(
    'monitorings', 'by_tender_id', monitoring_by_tender_id, language='python')


def monitoring_mode_by_tender_id(doc):
    if doc.get("doc_type") == "Monitoring" and doc.get("mode") == 'test' and doc["status"] not in ('draft', 'cancelled'):
        data = {k: doc[k] for k in ("status",) if doc.get(k) is not None}
        yield (doc['tender_id'], doc['dateCreated']), data


test_monitorings_by_tender_id_view = ViewDefinition(
    'monitorings', 'test_by_tender_id', monitoring_mode_by_tender_id, language='python')


def monitoring_draft_by_tender_id(doc):
    if doc.get("doc_type") == "Monitoring" and "mode" not in doc:
        data = {k: doc[k] for k in ("status",) if doc.get(k) is not None}
        yield (doc['tender_id'], doc['dateCreated']), data


draft_monitorings_by_tender_id_view = ViewDefinition(
    'monitorings', 'draft_by_tender_id', monitoring_draft_by_tender_id, language='python')
