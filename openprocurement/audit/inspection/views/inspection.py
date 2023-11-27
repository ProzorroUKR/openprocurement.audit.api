from logging import getLogger
from openprocurement.audit.api.views.base import APIResource, MongodbResourceListing, json_view
from openprocurement.audit.api.utils import (
    context_unpack,
    generate_id,
)
from openprocurement.audit.inspection.utils import (
    save_inspection,
    apply_patch,
    generate_inspection_id,
    op_resource,
)
from openprocurement.audit.inspection.validation import validate_inspection_data, validate_patch_inspection_data
from openprocurement.audit.monitoring.utils import set_author

LOGGER = getLogger(__name__)


@op_resource(name='Inspections', path='/inspections')
class InspectionsResource(MongodbResourceListing):

    def __init__(self, request, context):
        super(InspectionsResource, self).__init__(request, context)
        self.listing_name = "Inspections"
        self.listing_default_fields = {"dateModified"}
        self.listing_allowed_fields = {"dateCreated", "dateModified", "inspection_id"}
        self.db_listing_method = request.registry.mongodb.inspection.list

    @json_view(content_type='application/json',
               permission='create_inspection',
               validators=(validate_inspection_data,))
    def post(self):
        inspection = self.request.validated['inspection']
        inspection.id = generate_id()
        inspection.inspection_id = generate_inspection_id(self.request)
        set_author(inspection.documents, self.request, 'author')
        self.request.validated["inspection"] = inspection
        self.request.validated["inspection_src"] = {}
        save_inspection(
            self.request,
            insert=True
        )
        LOGGER.info('Created inspection {}'.format(inspection.id),
                    extra=context_unpack(self.request,
                                         {'MESSAGE_ID': 'inspection_create'},
                                         {'MONITORING_ID': inspection.id}))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url(
            'Inspection', inspection_id=inspection.id)
        return {'data': inspection.serialize('view')}


@op_resource(name='Inspection', path='/inspections/{inspection_id}')
class InspectionResource(APIResource):

    @json_view(permission='view_inspection')
    def get(self):
        inspection = self.request.validated['inspection']
        return {'data': inspection.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_inspection_data,),
               permission='edit_inspection')
    def patch(self):
        inspection = self.request.validated['inspection']
        apply_patch(self.request, src=self.request.validated['inspection_src'])
        LOGGER.info('Updated inspection {}'.format(inspection.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'inspection_patch'}))
        return {'data': inspection.serialize('view')}
