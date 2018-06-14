from openprocurement.api.utils import (
    context_unpack,
    decrypt,
    encrypt,
    get_now,
    generate_id,
    json_view,
    error_handler,
    APIResourceListing,
)

from openprocurement.audit.api.constraints import (
    MONITORING_TIME,
    ELIMINATION_PERIOD_TIME,
    ELIMINATION_PERIOD_NO_VIOLATIONS_TIME
)
from openprocurement.audit.api.utils import (
    save_monitoring,
    monitoring_serialize,
    apply_patch,
    op_resource,
    APIResource,
    generate_monitoring_id,
    generate_period,
    set_ownership,
    set_author,
    upload_objects_documents,
)
from openprocurement.audit.api.design import (
    monitorings_real_by_dateModified_view,
    monitorings_test_by_dateModified_view,
    monitorings_by_dateModified_view,
    monitorings_real_by_local_seq_view,
    monitorings_test_by_local_seq_view,
    monitorings_by_local_seq_view,
    monitorings_by_status_dateModified_view,
    monitorings_real_by_status_dateModified_view,
    monitorings_test_by_status_dateModified_view,
)
from openprocurement.audit.api.validation import (
    validate_monitoring_data,
    validate_patch_monitoring_data,
    validate_patch_monitoring_status,
    validate_credentials_generate
)
from openprocurement.audit.api.design import FIELDS
from logging import getLogger

LOGGER = getLogger(__name__)

VIEW_MAP = {
    u'': monitorings_real_by_dateModified_view,
    u'test': monitorings_test_by_dateModified_view,
    u'_all_': monitorings_by_dateModified_view,
}
STATUS_VIEW_MAP = {
    u'': monitorings_real_by_status_dateModified_view,
    u'test': monitorings_test_by_status_dateModified_view,
    u'_all_': monitorings_by_status_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': monitorings_real_by_local_seq_view,
    u'test': monitorings_test_by_local_seq_view,
    u'_all_': monitorings_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
    u'status': STATUS_VIEW_MAP,
}


@op_resource(name='Monitorings', path='/monitorings')
class MonitoringsResource(APIResourceListing):

    def __init__(self, request, context):
        super(MonitoringsResource, self).__init__(request, context)

        self.VIEW_MAP = VIEW_MAP
        self.STATUS_VIEW_MAP = STATUS_VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = monitoring_serialize
        self.object_name_for_listing = 'Monitorings'
        self.log_message_id = 'monitoring_list_custom'

    @json_view(content_type='application/json',
               permission='create_monitoring',
               validators=(validate_monitoring_data,))
    def post(self):
        monitoring = self.request.validated['monitoring']
        monitoring.id = generate_id()
        monitoring.monitoring_id = generate_monitoring_id(get_now(), self.db, self.server_id)
        save_monitoring(self.request, date_modified=monitoring.dateCreated)
        LOGGER.info('Created monitoring {}'.format(monitoring.id),
                    extra=context_unpack(self.request,
                                         {'MESSAGE_ID': 'monitoring_create'},
                                         {'MONITORING_ID': monitoring.id}))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Monitoring', monitoring_id=monitoring.id)
        return {'data': monitoring.serialize('view')}


@op_resource(name='Monitoring', path='/monitorings/{monitoring_id}')
class MonitoringResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        monitoring = self.request.validated['monitoring']
        return {'data': monitoring.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_monitoring_data, validate_patch_monitoring_status),
               permission='edit_monitoring')
    def patch(self):
        monitoring = self.request.validated['monitoring']
        monitoring_old_status = monitoring.status

        apply_patch(self.request, save=False, src=self.request.validated['monitoring_src'])

        now = get_now()
        if monitoring_old_status == 'draft' and monitoring.status == 'active':
            set_author(monitoring.decision.documents, self.request, 'author')
            monitoring.monitoringPeriod = generate_period(now, MONITORING_TIME, self.context)
            monitoring.decision.datePublished = now
        elif monitoring_old_status == 'active' and monitoring.status == 'addressed':
            set_author(monitoring.conclusion.documents, self.request, 'author')
            monitoring.conclusion.datePublished = now
            monitoring.eliminationPeriod = generate_period(now, ELIMINATION_PERIOD_TIME, self.context)
        elif monitoring_old_status == 'active' and monitoring.status == 'declined':
            monitoring.eliminationPeriod = generate_period(now, ELIMINATION_PERIOD_NO_VIOLATIONS_TIME, self.context)
            monitoring.conclusion.datePublished = now
        elif monitoring_old_status == 'addressed' and monitoring.status == 'completed':
            monitoring.eliminationReport.datePublished = now
            monitoring.eliminationReport.eliminationResolution = now
        elif any([
            monitoring_old_status == 'draft' and monitoring.status == 'cancelled',
            monitoring_old_status == 'active' and monitoring.status == 'stopped',
            monitoring_old_status == 'declined' and monitoring.status == 'stopped',
            monitoring_old_status == 'addressed' and monitoring.status == 'stopped'
        ]):
            set_author(monitoring.cancellation.documents, self.request, 'author')
            monitoring.cancellation.datePublished = now

        # download (change urls of) documents for Decision, Conclusion, etc.
        raw_data = self.request.json.get("data", {})
        for key in raw_data.keys():
            if hasattr(getattr(monitoring, key, None), "documents") and "documents" in raw_data[key]:
                upload_objects_documents(self.request, getattr(monitoring, key), key=key)

        save_monitoring(self.request, date_modified=now)
        LOGGER.info('Updated monitoring {}'.format(monitoring.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'monitoring_patch'}))
        return {'data': monitoring.serialize('view')}


@op_resource(name='Monitoring credentials',
             path='/monitorings/{monitoring_id}/credentials',
             description="Monitoring credentials")
class MonitoringCredentialsResource(APIResource):
    @json_view(permission='generate_credentials', validators=(validate_credentials_generate,))
    def patch(self):
        monitoring = self.request.validated['monitoring']

        set_ownership(monitoring, self.request, 'tender_owner')
        if save_monitoring(self.request):
            self.LOGGER.info('Generate Monitoring credentials {}'.format(monitoring.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'monitoring_patch'}))
            return {
                'data': monitoring.serialize('view'),
                'access': {
                    'token': monitoring.tender_owner_token
                }
            }
