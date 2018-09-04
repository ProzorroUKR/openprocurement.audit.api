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

monitorings_by_dateModified_view = ViewDefinition('monitorings', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && doc.status != 'draft') {
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
    if(doc.doc_type == 'Monitoring' && !doc.mode && doc.status != 'draft') {
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
    if(doc.doc_type == 'Monitoring' && doc.mode == 'test' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

monitorings_real_draft_by_dateModified_view = ViewDefinition('monitorings', 'real_draft_by_dateModified', '''function(doc) {
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

monitorings_all_draft_by_dateModified_view = ViewDefinition('monitorings', 'draft_by_dateModified', '''function(doc) {
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

monitorings_by_local_seq_view = ViewDefinition('monitorings', 'by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && doc.status != 'draft') {
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
    if(doc.doc_type == 'Monitoring' && !doc.mode && doc.status != 'draft') {
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
    if(doc.doc_type == 'Monitoring' && doc.mode == 'test' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

monitorings_real_draft_by_local_seq_view = ViewDefinition('monitorings', 'real_draft_by_local_seq', '''function(doc) {
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

monitorings_all_draft_by_local_seq_view = ViewDefinition('monitorings', 'draft_by_local_seq', '''function(doc) {
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


MONITORINGS_BY_TENDER_FIELDS = [
    'status',
]

monitorings_by_tender_id_view = ViewDefinition('monitorings', 'by_tender_id', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && !doc.mode && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.tender_id, doc.dateCreated], data);
    }
}''' % MONITORINGS_BY_TENDER_FIELDS)

test_monitorings_by_tender_id_view = ViewDefinition('monitorings', 'test_by_tender_id', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && doc.mode == 'test' && doc.status != 'draft') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.tender_id, doc.dateCreated], data);
    }
}''' % MONITORINGS_BY_TENDER_FIELDS)

draft_monitorings_by_tender_id_view = ViewDefinition('monitorings', 'draft_by_tender_id', '''function(doc) {
    if(doc.doc_type == 'Monitoring' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.tender_id, doc.dateCreated], data);
    }
}''' % MONITORINGS_BY_TENDER_FIELDS)
