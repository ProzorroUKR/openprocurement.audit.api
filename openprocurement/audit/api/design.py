# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition
from openprocurement.api import design


FIELDS = [
    'tender_id',
]
CHANGES_FIELDS = FIELDS + [
    'dateModified',
]


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


monitors_by_status_dateModified_view = ViewDefinition('monitors', 'by_status_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitor') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.status, doc.dateModified], data);
    }
}''' % FIELDS)

monitors_real_by_status_dateModified_view = ViewDefinition('monitors', 'real_by_status_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitor' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.status, doc.dateModified], data);
    }
}''' % FIELDS)

monitors_test_by_status_dateModified_view = ViewDefinition('monitors', 'test_by_status_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitor' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.status, doc.dateModified], data);
    }
}''' % FIELDS)

monitors_by_dateModified_view = ViewDefinition('monitors', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitor') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitors_real_by_dateModified_view = ViewDefinition('monitors', 'real_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitor' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitors_test_by_dateModified_view = ViewDefinition('monitors', 'test_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitor' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitors_by_local_seq_view = ViewDefinition('monitors', 'by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitor') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

monitors_real_by_local_seq_view = ViewDefinition('monitors', 'real_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitor' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

monitors_test_by_local_seq_view = ViewDefinition('monitors', 'test_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitor' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)
