# -*- coding: utf-8 -*-
from couchdb.design import ViewDefinition

from openprocurement.audit.api import design


def add_design():
    for i, j in globals().items():
        if "_view" in i:
            setattr(design, i, j)


FIELDS = ['inspection_id']
CHANGES_FIELDS = FIELDS + ['dateModified']

# INSPECTIONS
# the view below is used for an internal system monitoring
inspections_all_view = ViewDefinition('inspections', 'all', '''function(doc) {
    if(doc.doc_type == 'Inspection') {
        emit(doc.inspection_id, null);
    }
}''')


inspections_real_by_dateModified_view = ViewDefinition('inspections', 'real_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Inspection' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

inspections_test_by_dateModified_view = ViewDefinition('inspections', 'test_by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Inspection' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

inspections_by_dateModified_view = ViewDefinition('inspections', 'by_dateModified', '''function(doc) {
    if(doc.doc_type == 'Inspection') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc.dateModified, data);
    }
}''' % FIELDS)

inspections_real_by_local_seq_view = ViewDefinition('inspections', 'real_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Inspection' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

inspections_test_by_local_seq_view = ViewDefinition('inspections', 'test_by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Inspection' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)

inspections_by_local_seq_view = ViewDefinition('inspections', 'by_local_seq', '''function(doc) {
    if(doc.doc_type == 'Inspection') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        emit(doc._local_seq, data);
    }
}''' % CHANGES_FIELDS)


inspections_real_by_monitoring_id_view = ViewDefinition('monitorings', 'by_monitoring_id', '''function(doc) {
    if(doc.doc_type == 'Inspection' && !doc.mode) {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        for(var i=0;i<doc.monitoring_ids.length;i++){
            emit([doc.monitoring_ids[i], doc.dateCreated], data);
        }
    }
}''' % CHANGES_FIELDS)


inspections_real_by_monitoring_id_total_view = ViewDefinition(
    inspections_real_by_monitoring_id_view.design,
    inspections_real_by_monitoring_id_view.name + "_total",
    inspections_real_by_monitoring_id_view.map_fun,
    "_count"
)

inspections_test_by_monitoring_id_view = ViewDefinition('monitorings', 'test_by_monitoring_id', '''function(doc) {
    if(doc.doc_type == 'Inspection' && doc.mode == 'test') {
        var fields=%s, data={};
        for (var i in fields) {
            if (doc[fields[i]]) {
                data[fields[i]] = doc[fields[i]]
            }
        }
        for(var i=0;i<doc.monitoring_ids.length;i++){
            emit([doc.monitoring_ids[i], doc.dateCreated], data);
        }
    }
}''' % CHANGES_FIELDS)


inspections_test_by_monitoring_id_total_view = ViewDefinition(
    inspections_test_by_monitoring_id_view.design,
    inspections_real_by_monitoring_id_view.name + "_total",
    inspections_real_by_monitoring_id_view.map_fun,
    "_count"
)
