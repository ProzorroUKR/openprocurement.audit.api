# -*- coding: utf-8 -*-

from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
)


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, 'g:admins', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request


def get_item(parent, key, request):
    request.validated['{}_id'.format(key)] = request.matchdict['{}_id'.format(key)]
    plural = '{}ies'.format(key[0:-1]) if key[-1] == 'y' else '{}s'.format(key)
    items = [i for i in getattr(parent, plural, []) if i.id == request.matchdict['{}_id'.format(key)]]
    if not items:
        from openprocurement.audit.api.utils import error_handler
        request.errors.add('url', '{}_id'.format(key), 'Not Found')
        request.errors.status = 404
        raise error_handler(request)
    else:
        if key == 'document':
            request.validated[plural] = items
        item = items[-1]
        request.validated[key] = item
        request.validated['id'] = request.matchdict['{}_id'.format(key)]
        item.__parent__ = parent
        return item


def factory(request):
    root = Root(request)
    return root
