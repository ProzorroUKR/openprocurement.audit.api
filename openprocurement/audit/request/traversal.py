# -*- coding: utf-8 -*-
from pyramid.security import (
    Allow,
    Everyone,
)

from openprocurement.audit.api.constants import SAS_ROLE, PUBLIC_ROLE
from openprocurement.audit.api.traversal import get_item


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, "view_listing"),
        (Allow, Everyone, "view_request"),
        (Allow, "g:%s" % PUBLIC_ROLE, "create_request"),
        (Allow, "g:%s" % SAS_ROLE, "edit_request"),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def factory(request):
    request.validated["request_src"] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get("request_id"):
        return root
    request.validated["request_id"] = request.matchdict["request_id"]
    request.request.__parent__ = root
    request.validated["request"] = request.validated["db_doc"] = request.request
    if request.method != "GET":
        request.validated["request_src"] = request.request.serialize("plain")
    if request.matchdict.get("document_id"):
        return get_item(request.request, "document", request)
    return request.request
