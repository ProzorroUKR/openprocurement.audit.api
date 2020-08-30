from logging import getLogger

from openprocurement.audit.api.utils import APIResource, APIResourceListing, json_view
from openprocurement.audit.api.utils import (
    context_unpack,
    get_now,
    generate_id,
)
from openprocurement.audit.inspection.design import (
    inspections_real_by_dateModified_view,
    inspections_test_by_dateModified_view,
    inspections_by_dateModified_view,
    inspections_real_by_local_seq_view,
    inspections_test_by_local_seq_view,
    inspections_by_local_seq_view,
    FIELDS,
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
VIEW_MAP = {
    u'': inspections_real_by_dateModified_view,
    u'test': inspections_test_by_dateModified_view,
    u'_all_': inspections_by_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': inspections_real_by_local_seq_view,
    u'test': inspections_test_by_local_seq_view,
    u'_all_': inspections_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
}


@op_resource(name='Inspections', path='/inspections')
class InspectionsResource(APIResourceListing):
    
    def __init__(self, request, context):
        super(InspectionsResource, self).__init__(request, context)

        self.VIEW_MAP = VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = inspection_serialize
        self.object_name_for_listing = 'Inspections'
        self.log_message_id = 'inspections_list_custom'

    @json_view(content_type='application/json',
               permission='create_inspection',
               validators=(validate_inspection_data,))
    def post(self):
        inspection = self.request.validated['inspection']
        inspection.id = generate_id()
        inspection.inspection_id = generate_inspection_id(get_now(), self.db, self.server_id)
        set_author(inspection.documents, self.request, 'author')
        save_inspection(self.request, date_modified=inspection.dateCreated)
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
