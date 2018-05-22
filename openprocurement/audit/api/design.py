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


# the view below is used for an internal system monitoring
monitorings_all_view = ViewDefinition('monitorings', 'all', '''function(doc) {
    if(doc.doc_type == 'Monitoring') {
        emit(doc.monitoring_id, null);
    }
}''')


monitorings_by_status_dateModified_view = ViewDefinition('monitorings', 'by_status_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.status, doc.dateModified], data);
    }
}''' % FIELDS)

monitorings_real_by_status_dateModified_view = ViewDefinition('monitorings', 'real_by_status_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.status, doc.dateModified], data);
    }
}''' % FIELDS)

monitorings_test_by_status_dateModified_view = ViewDefinition('monitorings', 'test_by_status_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.status, doc.dateModified], data);
    }
}''' % FIELDS)

monitorings_by_dateModified_view = ViewDefinition('monitorings', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitorings_real_by_dateModified_view = ViewDefinition('monitorings', 'real_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitorings_test_by_dateModified_view = ViewDefinition('monitorings', 'test_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitorings_by_local_seq_view = ViewDefinition('monitorings', 'by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitoring') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

monitorings_real_by_local_seq_view = ViewDefinition('monitorings', 'real_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

monitorings_test_by_local_seq_view = ViewDefinition('monitorings', 'test_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)
