# -*- coding: utf-8 -*-
from openprocurement.api.traversal import get_item

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
        (Allow, Everyone, 'view_monitor'),
        (Allow, Everyone, 'revision_monitor'),
        (Allow, 'g:brokers', 'generate_credentials'),
        (Allow, 'g:sas', 'create_monitor'),
        (Allow, 'g:sas', 'upload_monitor_documents'),
        (Allow, 'g:sas', 'create_dialogue'),
        (Allow, 'g:sas', 'upload_dialogue_documents'),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def factory(request):
    request.validated['monitor_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('monitor_id'):
        return root
    request.validated['monitor_id'] = request.matchdict['monitor_id']
    request.monitor.__parent__ = root
    request.validated['monitor'] = request.validated['db_doc'] = request.monitor
    if request.method != 'GET':
        request.validated['monitor_src'] = request.monitor.serialize('plain')
    if 'decision' in request.path.split('/'):
        return decision_factory(request)
    elif 'conclusion' in request.path.split('/'):
        return conclusion_factory(request)
    elif request.matchdict.get('dialogue_id'):
        return dialogue_factory(request)
    elif request.matchdict.get('document_id'):
        return get_item(request.monitor, 'document', request)
    return request.monitor


def dialogue_factory(request):
    dialogue = get_item(request.monitor, 'dialogue', request)
    if request.matchdict.get('document_id'):
        return get_item(dialogue, 'document', request)
    return dialogue


def decision_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitor.decision, 'document', request)
    return request.monitor.decision


def conclusion_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitor.conclusion, 'document', request)
    return request.monitor.conclusion
