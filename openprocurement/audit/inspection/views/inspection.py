from logging import getLogger
from functools import partial
from openprocurement.audit.inspection.database import list_inspections
from openprocurement.audit.api.utils import APIResource, APIResourceListing, json_view
from openprocurement.audit.api.utils import (
    context_unpack,
    get_now,
    generate_id,
)
from openprocurement.audit.inspection.utils import (
    save_inspection,
    apply_patch,
    generate_inspection_id,
    inspection_serialize,
    op_resource,
)
from openprocurement.audit.inspection.validation import validate_inspection_data, validate_patch_inspection_data
from openprocurement.audit.monitoring.utils import set_author

LOGGER = getLogger(__name__)


@op_resource(name='Inspections', path='/inspections')
class InspectionsResource(APIResourceListing):

    listing_name = "Inspections"
    db_listing_method = list_inspections
    listing_safe_fields = {"id", "dateModified", "inspection_id"}

    def get_listing_serialize(self):
        serialize = partial(inspection_serialize, request=self.request)
        return serialize

    @json_view(content_type='application/json',
               permission='create_inspection',
               validators=(validate_inspection_data,))
    def post(self):
        inspection = self.request.validated['inspection']
        inspection.id = generate_id()
        inspection.inspection_id = generate_inspection_id(get_now())
        set_author(inspection.documents, self.request, 'author')
        save_inspection(
            self.request,
            date_modified=inspection.dateCreated,
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
        LOGGER.info('Updated monitoring {}'.format(inspection.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'inspection_patch'}))
        return {'data': inspection.serialize('view')}
