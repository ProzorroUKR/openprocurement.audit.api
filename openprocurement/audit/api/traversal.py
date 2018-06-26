# -*- coding: utf-8 -*-
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Everyone,
)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, 'view_listing'),
        (Allow, Everyone, 'view_monitoring'),
        (Allow, Everyone, 'revision_monitoring'),
        (Allow, 'g:brokers', 'generate_credentials'),
        (Allow, 'g:risk_indicators', 'create_monitoring'),
        (Allow, 'g:sas', 'create_monitoring'),
        (Allow, 'g:sas', 'edit_monitoring'),
        (Allow, 'g:sas', 'upload_monitoring_documents'),
        (Allow, 'g:sas', 'create_dialogue'),
        (Allow, 'g:sas', 'edit_dialogue'),
        (Allow, 'g:sas', 'upload_dialogue_documents'),
        (Allow, 'g:sas', 'create_party'),
        (Allow, 'g:sas', 'edit_party'),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def get_item(parent, key, request):
    request.validated['{}_id'.format(key)] = request.matchdict['{}_id'.format(key)]
    plural = '{}ies'.format(key[0:-1]) if key[-1] == 'y' else '{}s'.format(key)
    items = [i for i in getattr(parent, plural, []) if i.id == request.matchdict['{}_id'.format(key)]]
    if not items:
        from openprocurement.api.utils import error_handler
        request.errors.add('url', '{}_id'.format(key), 'Not Found')
        request.errors.status = 404
        raise error_handler(request.errors)
    else:
        if key == 'document':
            request.validated[plural] = items
        item = items[-1]
        request.validated[key] = item
        request.validated['id'] = request.matchdict['{}_id'.format(key)]
        item.__parent__ = parent
        return item


def factory(request):
    request.validated['monitoring_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('monitoring_id'):
        return root
    request.validated['monitoring_id'] = request.matchdict['monitoring_id']
    request.monitoring.__parent__ = root
    request.validated['monitoring'] = request.validated['db_doc'] = request.monitoring
    if request.method != 'GET':
        request.validated['monitoring_src'] = request.monitoring.serialize('plain')
    if 'decision' in request.path.split('/'):
        return decision_factory(request)
    elif 'conclusion' in request.path.split('/'):
        return conclusion_factory(request)
    elif 'eliminationReport' in request.path.split('/'):
        return elimination_factory(request)
    elif 'appeal' in request.path.split('/'):
        return appeal_factory(request)
    elif request.matchdict.get('dialogue_id'):
        return dialogue_factory(request)
    elif request.matchdict.get('party_id'):
        return get_item(request.monitoring, 'party', request)
    elif request.matchdict.get('document_id'):
        return get_item(request.monitoring, 'document', request)
    return request.monitoring


def appeal_factory(request):
    if request.monitoring.appeal:
        if request.matchdict.get('document_id'):
            return get_item(request.monitoring.appeal, 'document', request)
        return request.monitoring.appeal
    return request.monitoring


def elimination_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.eliminationReport, 'document', request)
    if request.method == "PUT":
        return request.monitoring
    else:
        return request.monitoring.eliminationReport


def dialogue_factory(request):
    dialogue = get_item(request.monitoring, 'dialogue', request)
    if request.matchdict.get('document_id'):
        return get_item(dialogue, 'document', request)
    return dialogue


def decision_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.decision, 'document', request)
    return request.monitoring.decision


def conclusion_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.conclusion, 'document', request)
    return request.monitoring.conclusion
