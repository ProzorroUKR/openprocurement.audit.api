# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition

from openprocurement.audit.api import design


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


FIELDS = [
    "requestId",
    "description",
    "violationTypes",
    "answer",
    "dateAnswered",
    "dateCreated",
    "parties",
]
CHANGES_FIELDS = FIELDS + ["dateModified"]

# REQUESTS
# the view below is used for an internal system monitoring
requests_all_view = ViewDefinition(
    "requests", "all", """function(doc) {
    if(doc.doc_type == 'Request') {
        emit(doc.requestId, null);
    }
}""")

requests_real_by_dateModified_view = ViewDefinition(
    "requests", "real_by_dateModified", """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}""" % FIELDS)

requests_real_answered_by_dateModified_view = ViewDefinition(
    "requests", "real_answered_by_dateModified", """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode && 'answer' in doc) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}""" % FIELDS)

requests_real_not_answered_by_dateModified_view = ViewDefinition(
    "requests", "real_not_answered_by_dateModified", """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode && !('answer' in doc)) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}""" % FIELDS)

requests_test_by_dateModified_view = ViewDefinition(
    "requests", "test_by_dateModified", """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}""" % FIELDS)

requests_test_answered_by_dateModified_view = ViewDefinition(
    "requests", "test_answered_by_dateModified", """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test' && 'answer' in doc) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}""" % FIELDS)

requests_test_not_answered_by_dateModified_view = ViewDefinition(
    "requests", "test_not_answered_by_dateModified", """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test' && !('answer' in doc)) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}""" % FIELDS)

requests_real_by_local_seq_view = ViewDefinition(
    "requests", "real_by_local_seq", """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}"""% CHANGES_FIELDS)

requests_real_answered_by_local_seq_view = ViewDefinition(
    "requests", "real_answered__by_local_seq", """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode && 'answer' in doc) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}"""% CHANGES_FIELDS)

requests_real_not_answered_by_local_seq_view = ViewDefinition(
    "requests", "real_not_answered_by_local_seq", """function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode && !('answer' in doc)) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}"""% CHANGES_FIELDS)

requests_test_by_local_seq_view = ViewDefinition(
    "requests", "test_by_local_seq", """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}""" % CHANGES_FIELDS)

requests_test_answered_by_local_seq_view = ViewDefinition(
    "requests", "test_answered_by_local_seq", """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test' && 'answer' in doc) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}""" % CHANGES_FIELDS)

requests_test_not_answered_by_local_seq_view = ViewDefinition(
    "requests", "test_not_answered_by_local_seq", """function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test' && !('answer' in doc)) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}""" % CHANGES_FIELDS)

requests_real_by_tender_id_view = ViewDefinition(
    'requests', 'real_by_tender_id', '''function(doc) {
    if(doc.doc_type == 'Request' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.tenderId, doc.dateCreated], data);
    }
}''' % CHANGES_FIELDS)

requests_real_by_tender_id_total_view = ViewDefinition(
    requests_real_by_tender_id_view.design,
    requests_real_by_tender_id_view.name + "_total",
    requests_real_by_tender_id_view.map_fun,
    "_count"
)


requests_test_by_tender_id_view = ViewDefinition(
    'requests', 'test_by_tender_id', '''function(doc) {
    if(doc.doc_type == 'Request' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit([doc.tenderId, doc.dateCreated], data);
    }
}''' % CHANGES_FIELDS)

requests_test_by_tender_id_total_view = ViewDefinition(
    requests_test_by_tender_id_view.design,
    requests_test_by_tender_id_view.name + "_total",
    requests_test_by_tender_id_view.map_fun,
    "_count"
)
