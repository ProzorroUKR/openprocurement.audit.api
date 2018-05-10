# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    save_monitor,
    op_resource,
    apply_patch,
    APIResource,
    set_ownership,
    set_documents_of_type
)
from openprocurement.api.utils import (
    get_file,
    update_file_content_type,
    upload_file,
    context_unpack,
    json_view
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)
from openprocurement.audit.api.validation import (
    validate_document_decision_upload_allowed,
    validate_document_conclusion_upload_allowed
)


class MonitorsDocumentBaseResource(APIResource):
    document_of = None

    @json_view(permission='view_monitor')
    def collection_get(self):
        """
        Monitor Documents List
        """
        documents = self.context.documents
        if not self.request.params.get('all', ''):
            documents_top = dict([(document.id, document) for document in documents]).values()
            documents = sorted(documents_top, key=lambda i: i['dateModified'])
        return {'data': [document.serialize("view") for document in documents]}

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_upload,))
    def collection_post(self):
        """
        Monitor Document Upload
        """
        document = upload_file(self.request)
        set_documents_of_type(document, self.document_of)
        set_ownership(document, self.request, 'author')
        documents = self.context.documents
        documents.append(document)
        if save_monitor(self.request):
            self.LOGGER.info('Created {} monitor document {}'.format(self.document_of, document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitor_document_create'},
                                                  {'DOCUMENT_ID': document.id}))
            route = self.request.matched_route.name.replace("collection_", "")
            location = self.request.current_route_url(document_id=document.id, _route_name=route, _query={})
            self.request.response.status = 201
            self.request.response.headers['Location'] = location
            return {'data': document.serialize("view")}

    @json_view(permission='view_monitor')
    def get(self):
        """
        Monitor Document Read
        """
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        documents = self.request.validated['documents']
        versions_data = [i.serialize("view") for i in documents if i.url != document.url]
        document_data = document.serialize("view")
        document_data['previousVersions'] = versions_data
        return {'data': document_data}

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_update,))
    def put(self):
        """
        Monitor Document Update
        """
        parent = self.request.context.__parent__
        document = upload_file(self.request)
        set_documents_of_type(document, self.document_of)
        set_ownership(document, self.request, 'author')
        parent.documents.append(document)
        if save_monitor(self.request):
            self.LOGGER.info('Updated {} monitor document {}'.format(self.document_of, document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitor_document_put'},
                                                  {'DOCUMENT_ID': document.id}))
            return {'data': document.serialize("view")}

    @json_view(content_type='application/json',
               permission='edit_monitor_documents',
               validators=(validate_patch_document_data,))
    def patch(self):
        """
        Monitor Document Update
        """
        document = self.request.context
        if apply_patch(self.request, src=document.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info('Updated {} monitor document {}'.format(self.document_of, document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitor_document_patch'},
                                                  {'DOCUMENT_ID': document.id}))
            return {'data': self.request.context.serialize("view")}


@op_resource(name='Monitor Decision Documents',
             collection_path='/monitors/{monitor_id}/decision/documents',
             path='/monitors/{monitor_id}/decision/documents/{document_id}',
             description="Monitor Decision related binary files (PDFs, etc.)")
class MonitorsDocumentDecisionResource(MonitorsDocumentBaseResource):
    document_of = 'decision'

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_upload, validate_document_decision_upload_allowed))
    def collection_post(self):
        return super(MonitorsDocumentDecisionResource, self).collection_post()

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_update, validate_document_decision_upload_allowed))
    def put(self):
        return super(MonitorsDocumentDecisionResource, self).put()


@op_resource(name='Monitor Conclusion Documents',
             collection_path='/monitors/{monitor_id}/conclusion/documents',
             path='/monitors/{monitor_id}/conclusion/documents/{document_id}',
             description="Monitor Conclusion related binary files (PDFs, etc.)")
class MonitorsDocumentConclusionResource(MonitorsDocumentBaseResource):
    document_of = 'conclusion'

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_upload, validate_document_conclusion_upload_allowed))
    def collection_post(self):
        return super(MonitorsDocumentConclusionResource, self).collection_post()

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_update, validate_document_conclusion_upload_allowed))
    def put(self):
        return super(MonitorsDocumentConclusionResource, self).put()


@op_resource(name='Monitor Dialogue Documents',
             collection_path='/monitors/{monitor_id}/dialogues/{dialogue_id}/documents',
             path='/monitors/{monitor_id}/dialogues/{dialogue_id}/documents/{document_id}',
             description="Monitor Conclusion related binary files (PDFs, etc.)")
class MonitorsDocumentDialogueResource(MonitorsDocumentBaseResource):
    document_of = 'dialogue'

    @json_view(permission='upload_dialogue_documents',
               validators=(validate_file_upload, validate_document_conclusion_upload_allowed,))
    def collection_post(self):
        return super(MonitorsDocumentDialogueResource, self).collection_post()

    @json_view(permission='upload_monitor_documents',
               validators=(validate_file_update, validate_document_conclusion_upload_allowed))
    def put(self):
        return super(MonitorsDocumentDialogueResource, self).put()


@op_resource(name='Monitor Elimination Report Documents',
             collection_path='/monitors/{monitor_id}/eliminationReport/documents',
             path='/monitors/{monitor_id}/eliminationReport/documents/{document_id}',
             description="Monitor Elimination Report related binary files (PDFs, etc.)")
class MonitorsDocumentEliminationResource(MonitorsDocumentBaseResource):
    document_of = 'eliminationReport'

    @json_view(permission='edit_elimination_report',
               validators=(validate_file_upload,))
    def collection_post(self):
        return super(MonitorsDocumentEliminationResource, self).collection_post()

    @json_view(permission='edit_elimination_report',
               validators=(validate_file_update,))
    def patch(self):
        return super(MonitorsDocumentEliminationResource, self).patch()

    @json_view(permission='edit_elimination_report',
               validators=(validate_file_update,))
    def put(self):
        return super(MonitorsDocumentEliminationResource, self).put()
