# -*- coding: utf-8 -*-
from openprocurement.audit.api.constants import (
    MONITORING_OBJECT_TYPE,
    CANCELLATION_OBJECT_TYPE,
    DECISION_OBJECT_TYPE,
    CONCLUSION_OBJECT_TYPE,
    APPEAL_OBJECT_TYPE,
    LIABILITY_OBJECT_TYPE,
    ELIMINATION_REPORT_OBJECT_TYPE,
    ELIMINATION_RESOLUTION_OBJECT_TYPE,
    POST_OBJECT_TYPE,
)
from openprocurement.audit.api.utils import (
    upload_file, get_file, context_unpack, APIResource, forbidden, op_resource, json_view
)
from openprocurement.audit.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)
from openprocurement.audit.monitoring.utils import (
    save_monitoring,
    apply_patch,
    set_author,
    op_resource
)
from openprocurement.audit.monitoring.validation import (
    validate_document_decision_status,
    validate_document_conclusion_status,
    validate_document_post_status,
)


class MonitoringsDocumentBaseResource(APIResource):
    document_type = None

    @json_view(permission='view_monitoring')
    def collection_get(self):
        """
        Monitoring Documents List
        """
        documents = self.context.documents
        if not self.request.params.get('all', ''):
            documents_top = dict([(document.id, document) for document in documents]).values()
            documents = sorted(documents_top, key=lambda i: i['dateModified'])
        return {'data': [document.serialize('view') for document in documents]}

    @json_view(permission='edit_monitoring',
               validators=(validate_file_upload,))
    def collection_post(self):
        """
        Monitoring Document Upload
        """
        document = upload_file(self.request)
        set_author(document, self.request, 'author')
        documents = self.context.documents
        documents.append(document)
        if save_monitoring(self.request):
            self.LOGGER.info('Created {} monitoring document {}'.format(self.document_type, document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitoring_document_create'},
                                                  {'DOCUMENT_ID': document.id}))
            route = self.request.matched_route.name.replace('collection_', '')
            location = self.request.current_route_url(document_id=document.id, _route_name=route, _query={})
            self.request.response.status = 201
            self.request.response.headers['Location'] = location
            return {'data': document.serialize('view')}

    @json_view(permission='view_monitoring')
    def get(self):
        """
        Monitoring Document Read
        """
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        documents = self.request.validated['documents']
        versions_data = [i.serialize('view') for i in documents if i.url != document.url]
        document_data = document.serialize('view')
        document_data['previousVersions'] = versions_data
        return {'data': document_data}

    @json_view(permission='edit_monitoring',
               validators=(validate_file_update,))
    def put(self):
        """
        Monitoring Document Update
        """
        parent = self.request.context.__parent__
        document = upload_file(self.request)
        set_author(document, self.request, 'author')
        parent.documents.append(document)
        if save_monitoring(self.request):
            self.LOGGER.info('Updated {} monitoring document {}'.format(self.document_type, document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitoring_document_put'},
                                                  {'DOCUMENT_ID': document.id}))
            return {'data': document.serialize('view')}

    @json_view(content_type='application/json',
               permission='edit_monitoring',
               validators=(validate_patch_document_data,))
    def patch(self):
        """
        Monitoring Document Update
        """
        document = self.request.context
        if apply_patch(self.request):
            self.LOGGER.info('Updated {} monitoring document {}'.format(self.document_type, document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitoring_document_patch'},
                                                  {'DOCUMENT_ID': document.id}))
            return {'data': self.request.context.serialize('view')}


@op_resource(name='Monitoring Documents',
             collection_path='/monitorings/{monitoring_id}/documents',
             path='/monitorings/{monitoring_id}/documents/{document_id}',
             description='Monitoring related binary files (PDFs, etc.)')
class MonitoringsDocumentResource(MonitoringsDocumentBaseResource):
    document_type = MONITORING_OBJECT_TYPE

@op_resource(name='Monitoring Cancellation Documents',
             collection_path='/monitorings/{monitoring_id}/cancellation/documents',
             path='/monitorings/{monitoring_id}/cancellation/documents/{document_id}',
             description='Monitoring Cancellation related binary files (PDFs, etc.)')
class MonitoringsCancellationDocumentResource(MonitoringsDocumentBaseResource):
    document_type = CANCELLATION_OBJECT_TYPE

@op_resource(name='Monitoring Decision Documents',
             collection_path='/monitorings/{monitoring_id}/decision/documents',
             path='/monitorings/{monitoring_id}/decision/documents/{document_id}',
             description='Monitoring Decision related binary files (PDFs, etc.)')
class MonitoringsDocumentDecisionResource(MonitoringsDocumentBaseResource):
    document_type = DECISION_OBJECT_TYPE

    @json_view(permission='edit_monitoring',
               validators=(validate_document_decision_status, validate_file_upload,))
    def collection_post(self):
        return super(MonitoringsDocumentDecisionResource, self).collection_post()

    @json_view(permission='edit_monitoring',
               validators=(validate_document_decision_status, validate_patch_document_data,))
    def patch(self):
        return super(MonitoringsDocumentDecisionResource, self).patch()

    @json_view(permission='edit_monitoring',
               validators=(validate_document_decision_status, validate_file_update,))
    def put(self):
        return super(MonitoringsDocumentDecisionResource, self).put()


@op_resource(name='Monitoring Conclusion Documents',
             collection_path='/monitorings/{monitoring_id}/conclusion/documents',
             path='/monitorings/{monitoring_id}/conclusion/documents/{document_id}',
             description='Monitoring Conclusion related binary files (PDFs, etc.)')
class MonitoringsDocumentConclusionResource(MonitoringsDocumentBaseResource):
    document_type = CONCLUSION_OBJECT_TYPE

    @json_view(permission='edit_monitoring',
               validators=(validate_document_conclusion_status, validate_file_upload,))
    def collection_post(self):
        return super(MonitoringsDocumentConclusionResource, self).collection_post()

    @json_view(permission='edit_monitoring',
               validators=(validate_document_conclusion_status, validate_patch_document_data,))
    def patch(self):
        return super(MonitoringsDocumentConclusionResource, self).patch()

    @json_view(permission='edit_monitoring',
               validators=(validate_document_conclusion_status, validate_file_update,))
    def put(self):
        return super(MonitoringsDocumentConclusionResource, self).put()


@op_resource(name='Monitoring Post Documents',
             collection_path='/monitorings/{monitoring_id}/posts/{post_id}/documents',
             path='/monitorings/{monitoring_id}/posts/{post_id}/documents/{document_id}',
             description='Monitoring Post related binary files (PDFs, etc.)')
class MonitoringsDocumentPostResource(MonitoringsDocumentBaseResource):
    document_type = POST_OBJECT_TYPE

    @json_view(permission='create_post',
               validators=(validate_document_post_status, validate_file_upload,))
    def collection_post(self):
        return super(MonitoringsDocumentPostResource, self).collection_post()

    @json_view(permission='create_post',
               validators=(validate_document_post_status, validate_patch_document_data,))
    def patch(self):
        return super(MonitoringsDocumentPostResource, self).patch()

    @json_view(permission='create_post',
               validators=(validate_document_post_status, validate_file_update,))
    def put(self):
        return super(MonitoringsDocumentPostResource, self).put()


@op_resource(name='Monitoring Elimination Report Documents',
             collection_path='/monitorings/{monitoring_id}/eliminationReport/documents',
             path='/monitorings/{monitoring_id}/eliminationReport/documents/{document_id}',
             description='Monitoring Elimination Report related binary files (PDFs, etc.)')
class MonitoringsDocumentEliminationResource(MonitoringsDocumentBaseResource):
    document_type = ELIMINATION_REPORT_OBJECT_TYPE

    @json_view(permission='create_elimination_report',
               validators=(validate_file_upload,))
    def collection_post(self):
        return super(MonitoringsDocumentEliminationResource, self).collection_post()

    @json_view(permission='create_elimination_report',
               validators=(validate_patch_document_data,))
    def patch(self):
        return super(MonitoringsDocumentEliminationResource, self).patch()

    @json_view(permission='create_elimination_report',
               validators=(validate_file_update,))
    def put(self):
        return super(MonitoringsDocumentEliminationResource, self).put()

@op_resource(name='Monitoring Elimination Resolution Documents',
             collection_path='/monitorings/{monitoring_id}/eliminationResolution/documents',
             path='/monitorings/{monitoring_id}/eliminationResolution/documents/{document_id}',
             description='Monitoring Elimination Resolution related binary files (PDFs, etc.)')
class MonitoringsDocumentEliminationResolutionResource(MonitoringsDocumentBaseResource):
    document_type = ELIMINATION_RESOLUTION_OBJECT_TYPE


@op_resource(name='Monitoring Appeal Documents',
             collection_path='/monitorings/{monitoring_id}/appeal/documents',
             path='/monitorings/{monitoring_id}/appeal/documents/{document_id}',
             description='Monitoring Appeal related binary files (PDFs, etc.)')
class AppealDocumentResource(MonitoringsDocumentBaseResource):
    document_type = APPEAL_OBJECT_TYPE

    @json_view(permission='create_appeal',
               validators=(validate_file_upload,))
    def collection_post(self):
        return super(AppealDocumentResource, self).collection_post()

    @json_view(permission='create_appeal',
               validators=(validate_patch_document_data,))
    def patch(self):
        return super(AppealDocumentResource, self).patch()

    @json_view(permission='create_appeal',
               validators=(validate_file_update,))
    def put(self):
        return super(AppealDocumentResource, self).put()


@op_resource(name='Monitoring LIABILITY Documents',
             collection_path='/monitorings/{monitoring_id}/liabilities/{liability_id}/documents',
             path='/monitorings/{monitoring_id}/liabilities/{liability_id}/documents/{document_id}',
             description='Monitoring Liability related binary files (PDFs, etc.)')
class LiabilityDocumentResource(MonitoringsDocumentBaseResource):
    document_type = LIABILITY_OBJECT_TYPE

    @json_view(permission='edit_monitoring',
               validators=(validate_file_upload,))
    def collection_post(self):
        return super(LiabilityDocumentResource, self).collection_post()

    @json_view(permission='edit_monitoring',
               validators=(validate_patch_document_data,))
    def patch(self):
        return super(LiabilityDocumentResource, self).patch()

    @json_view(permission='edit_monitoring',
               validators=(validate_file_update,))
    def put(self):
        return super(LiabilityDocumentResource, self).put()
