from openprocurement.api.utils import (
    context_unpack,
    decrypt,
    encrypt,
    get_now,
    generate_id,
    json_view,
    set_ownership,
    APIResourceListing
)
from openprocurement.audit.api.utils import (
    save_monitor,
    monitor_serialize,
    apply_patch,
    op_resource,
    APIResource
)
from openprocurement.audit.api.design import (
    monitors_real_by_dateModified_view,
    monitors_test_by_dateModified_view,
    monitors_by_dateModified_view,
    monitors_real_by_local_seq_view,
    monitors_test_by_local_seq_view,
    monitors_by_local_seq_view,
)
from openprocurement.audit.api.validation import validate_monitor_data, validate_patch_monitor_data
from openprocurement.audit.api.design import FIELDS
from logging import getLogger

LOGGER = getLogger(__name__)


VIEW_MAP = {
    u'': monitors_real_by_dateModified_view,
    u'test': monitors_test_by_dateModified_view,
    u'_all_': monitors_by_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': monitors_real_by_local_seq_view,
    u'test': monitors_test_by_local_seq_view,
    u'_all_': monitors_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
}


@op_resource(name='Monitors', path='/monitors')
class MonitorsResource(APIResourceListing):

    def __init__(self, request, context):
        super(MonitorsResource, self).__init__(request, context)
        # params for listing
        self.VIEW_MAP = VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = monitor_serialize
        self.object_name_for_listing = 'Monitors'
        self.log_message_id = 'monitor_list_custom'

    @json_view(content_type="application/json", permission='create_monitor', validators=(validate_monitor_data,))
    def post(self):
        monitor = self.request.validated['monitor']
        monitor.id = generate_id()

        set_ownership(monitor, self.request)
        self.request.validated['monitor'] = monitor
        self.request.validated['monitor_src'] = {}
        if save_monitor(self.request):
            LOGGER.info('Created monitor {}'.format(monitor.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'monitor_create'}, {'monitor_id': monitor.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('Monitor', monitor_id=monitor.id)
            return {
                'data': monitor.serialize("view"),
                'access': {
                    'token': monitor.owner_token
                }
            }
        
        
@op_resource(name='Monitor', path='/monitors/{monitor_id}')
class MonitorResource(APIResource):

    @json_view(permission='view_monitor')
    def get(self):
        monitor = self.request.validated['monitor']
        data = monitor.serialize('view')
        return {'data': data}

    @json_view(content_type="application/json", validators=(validate_patch_monitor_data,), permission='edit_monitor')
    def patch(self):
        print(self.request.authenticated_role)
        monitor = self.request.validated['monitor']
        apply_patch(self.request, src=self.request.validated['monitor_src'])
        LOGGER.info('Updated monitor {}'.format(monitor.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'monitor_patch'}))
        return {'data': monitor.serialize('view')}
