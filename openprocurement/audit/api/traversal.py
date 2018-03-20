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
        (Allow, 'g:sas', 'create_monitor'),
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
    monitor = request.monitor
    monitor.__parent__ = root
    request.validated['monitor'] = request.validated['db_doc'] = monitor
    if request.method != 'GET':
        request.validated['monitor_src'] = monitor.serialize('plain')
    if request.matchdict.get('document_id'):
        return get_item(monitor, 'document', request)
    request.validated['id'] = request.matchdict['monitor_id']
    return monitor
