# -*- coding: utf-8 -*-
from pyramid.security import (
    Allow,
    Everyone,
)

from openprocurement.audit.api.traversal import get_item


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, 'view_listing'),
        (Allow, Everyone, 'view_inspection'),
        (Allow, Everyone, 'revision_inspection'),
        (Allow, 'g:sas', 'create_inspection'),
        (Allow, 'g:sas', 'edit_inspection'),
    ]

    def __init__(self, request):
        self.request = request


def factory(request):
    request.validated['inspection_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('inspection_id'):
        return root
    request.validated['inspection_id'] = request.matchdict['inspection_id']
    request.inspection.__parent__ = root
    request.validated['inspection'] = request.validated['db_doc'] = request.inspection
    if request.method != 'GET':
        request.validated['inspection_src'] = request.inspection.serialize('plain')
    if request.matchdict.get('document_id'):
        return get_item(request.inspection, 'document', request)
    return request.inspection
