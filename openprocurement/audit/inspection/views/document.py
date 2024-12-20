from openprocurement.audit.api.utils import get_file, upload_file, context_unpack
from openprocurement.audit.api.views.base import APIResource, json_view
from openprocurement.audit.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data,
)
from openprocurement.audit.inspection.utils import (
    save_inspection,
    apply_patch,
    op_resource
)
from openprocurement.audit.monitoring.utils import set_author


@op_resource(name='Inspection Documents',
             collection_path='/inspections/{inspection_id}/documents',
             path='/inspections/{inspection_id}/documents/{document_id}',
             description="Inspection related binary files (PDFs, etc.)")
class InspectionsDocumentBaseResource(APIResource):

    @json_view(permission='view_inspection')
    def collection_get(self):
        documents = self.context.documents
        if not self.request.params.get('all', ''):
            documents_top = dict([(document.id, document) for document in documents]).values()
            documents = sorted(documents_top, key=lambda i: i['dateModified'])
        return {'data': [document.serialize("view") for document in documents]}

    @json_view(permission='edit_inspection',
               validators=(validate_file_upload,))
    def collection_post(self):
        document = upload_file(self.request)
        set_author(document, self.request, 'author')
        documents = self.context.documents
        documents.append(document)
        if save_inspection(self.request):
            self.LOGGER.info('Created inspection document {}'.format(document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'inspection_document_create'},
                                                  {'DOCUMENT_ID': document.id}))
            route = self.request.matched_route.name.replace("collection_", "")
            location = self.request.current_route_url(document_id=document.id, _route_name=route, _query={})
            self.request.response.status = 201
            self.request.response.headers['Location'] = location
            return {'data': document.serialize("view")}

    @json_view(permission='view_inspection')
    def get(self):
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        documents = self.request.validated['documents']
        versions_data = [i.serialize("view") for i in documents if i.url != document.url]
        document_data = document.serialize("view")
        document_data['previousVersions'] = versions_data
        return {'data': document_data}

    @json_view(permission='edit_inspection',
               validators=(validate_file_update,))
    def put(self):
        parent = self.request.context.__parent__
        document = upload_file(self.request)
        set_author(document, self.request, 'author')
        parent.documents.append(document)
        if save_inspection(self.request):
            self.LOGGER.info('Updated inspection document {}'.format(document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'inspection_document_put'},
                                                  {'DOCUMENT_ID': document.id}))
            return {'data': document.serialize("view")}

    @json_view(content_type='application/json',
               permission='edit_inspection',
               validators=(validate_patch_document_data,))
    def patch(self):
        document = self.request.context
        if apply_patch(self.request):
            self.LOGGER.info('Updated inspection document {}'.format(document.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'inspection_document_patch'},
                                                  {'DOCUMENT_ID': document.id}))
            return {'data': self.request.context.serialize("view")}
