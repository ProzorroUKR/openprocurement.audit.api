# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition

from openprocurement.audit.api import design


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


FIELDS = ["requestId"]
CHANGES_FIELDS = FIELDS + ["dateModified"]

# REQUESTS
# the view below is used for an internal system monitoring
requests_all_view = ViewDefinition(
    "requests",
    "all",
    """function(doc) {
    if(doc.doc_type == 'Request') {
        emit(doc.requestId, null);
    }
}""",
)


requests_real_by_dateModified_view = ViewDefinition(
    "requests",
    "real_by_dateModified",
    """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}"""
    % FIELDS,
)

requests_test_by_dateModified_view = ViewDefinition(
    "requests",
    "test_by_dateModified",
    """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}"""
    % FIELDS,
)

requests_by_dateModified_view = ViewDefinition(
    "requests",
    "by_dateModified",
    """function(doc) {
    if(doc.doc_type == 'Request') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}"""
    % FIELDS,
)

requests_real_by_local_seq_view = ViewDefinition(
    "requests",
    "real_by_local_seq",
    """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}"""
    % CHANGES_FIELDS,
)

requests_test_by_local_seq_view = ViewDefinition(
    "requests",
    "test_by_local_seq",
    """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}"""
    % CHANGES_FIELDS,
)

requests_by_local_seq_view = ViewDefinition(
    "requests",
    "by_local_seq",
    """function(doc) {
    if(doc.doc_type == 'Request') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}"""
    % CHANGES_FIELDS,
)
