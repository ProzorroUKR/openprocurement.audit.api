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
        (Allow, Everyone, 'view_monitoring'),
        (Allow, 'g:sas', 'view_draft_monitoring'),
        (Allow, 'g:risk_indicators', 'view_draft_monitoring'),
        (Allow, 'g:risk_indicators_api', 'view_draft_monitoring'),
        (Allow, Everyone, 'revision_monitoring'),
        (Allow, 'g:brokers', 'generate_credentials'),
        (Allow, 'g:risk_indicators', 'create_monitoring'),
        (Allow, 'g:sas', 'create_monitoring'),
        (Allow, 'g:sas', 'edit_monitoring'),
        (Allow, 'g:sas', 'create_party'),
        (Allow, 'g:sas', 'edit_party'),
        (Allow, 'g:sas', 'create_post'),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


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
    if 'cancellation' in request.path.split('/'):
        return cancellation_factory(request)
    elif 'conclusion' in request.path.split('/'):
        return conclusion_factory(request)
    elif 'eliminationReport' in request.path.split('/'):
        return elimination_factory(request)
    elif 'eliminationResolution' in request.path.split('/'):
        return elimination_resolution_factory(request)
    elif 'appeal' in request.path.split('/'):
        return appeal_factory(request)
    elif request.matchdict.get('liability_id'):
        return liability_factory(request)
    elif request.matchdict.get('post_id'):
        return post_factory(request)
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


def liability_factory(request):
    liability = get_item(request.monitoring, 'liability', request)
    if request.matchdict.get('document_id'):
        return get_item(liability, 'document', request)
    return liability


def elimination_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.eliminationReport, 'document', request)
    if request.method == "PUT":
        return request.monitoring
    else:
        return request.monitoring.eliminationReport

def elimination_resolution_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.eliminationResolution, 'document', request)
    return request.monitoring.eliminationResolution

def post_factory(request):
    post = get_item(request.monitoring, 'post', request)
    if request.matchdict.get('document_id'):
        return get_item(post, 'document', request)
    return post


def decision_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.decision, 'document', request)
    return request.monitoring.decision

def cancellation_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.cancellation, 'document', request)
    return request.monitoring.cancellation


def conclusion_factory(request):
    if request.matchdict.get('document_id'):
        return get_item(request.monitoring.conclusion, 'document', request)
    return request.monitoring.conclusion
