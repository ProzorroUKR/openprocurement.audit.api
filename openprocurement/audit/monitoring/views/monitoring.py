from logging import getLogger

from pyramid.security import ACLAllowed

from openprocurement.audit.api.constants import (
    MONITORING_TIME,
    ELIMINATION_PERIOD_TIME,
    ELIMINATION_PERIOD_NO_VIOLATIONS_TIME,
    DRAFT_STATUS,
    ACTIVE_STATUS,
    ADDRESSED_STATUS,
    DECLINED_STATUS,
    STOPPED_STATUS,
    CANCELLED_STATUS,
)
from openprocurement.audit.api.utils import (
    context_unpack, APIResource, APIResourceListing, json_view, forbidden, op_resource
)
from openprocurement.audit.api.utils import (
    generate_id,
)
from openprocurement.audit.monitoring.design import FIELDS
from openprocurement.audit.monitoring.design import (
    monitorings_real_by_dateModified_view,
    monitorings_test_by_dateModified_view,
    monitorings_by_dateModified_view,
    monitorings_real_by_local_seq_view,
    monitorings_test_by_local_seq_view,
    monitorings_by_local_seq_view,
    monitorings_real_draft_by_local_seq_view,
    monitorings_all_draft_by_local_seq_view,
    monitorings_real_draft_by_dateModified_view,
    monitorings_all_draft_by_dateModified_view,
    monitorings_real_count_view,
    monitorings_test_count_view,
)
from openprocurement.audit.monitoring.utils import (
    get_now, calculate_normalized_business_date, upload_objects_documents
)
from openprocurement.audit.monitoring.utils import (
    save_monitoring,
    monitoring_serialize,
    apply_patch,
    generate_monitoring_id,
    generate_period,
    set_ownership,
    set_author,
    get_monitoring_accelerator,
)
from openprocurement.audit.monitoring.validation import (
    validate_monitoring_data,
    validate_patch_monitoring_data,
    validate_credentials_generate
)

LOGGER = getLogger(__name__)

VIEW_MAP = {
    u'': monitorings_real_by_dateModified_view,
    u'test': monitorings_test_by_dateModified_view,
    u'real_draft': monitorings_real_draft_by_dateModified_view,
    u'all_draft': monitorings_all_draft_by_dateModified_view,
    u'_all_': monitorings_by_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': monitorings_real_by_local_seq_view,
    u'test': monitorings_test_by_local_seq_view,
    u'real_draft': monitorings_real_draft_by_local_seq_view,
    u'all_draft': monitorings_all_draft_by_local_seq_view,
    u'_all_': monitorings_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
}


@op_resource(name='Monitorings', path='/monitorings')
class MonitoringsResource(APIResourceListing):

    def __init__(self, request, context):
        super(MonitoringsResource, self).__init__(request, context)

        self.VIEW_MAP = VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = monitoring_serialize
        self.object_name_for_listing = 'Monitorings'
        self.log_message_id = 'monitoring_list_custom'

    def get(self):
        if self.request.params.get('mode') in ('real_draft', 'all_draft'):
            perm = self.request.has_permission('view_draft_monitoring')
            if not isinstance(perm, ACLAllowed):
                return forbidden(self.request)
        return super(MonitoringsResource, self).get()

    @json_view(content_type='application/json',
               permission='create_monitoring',
               validators=(validate_monitoring_data,))
    def post(self):
        monitoring = self.request.validated['monitoring']
        monitoring.id = generate_id()
        monitoring.monitoring_id = generate_monitoring_id(get_now(), self.db, self.server_id)
        if monitoring.decision:
            upload_objects_documents(self.request, monitoring.decision, key="decision")
            set_author(monitoring.decision.documents, self.request, 'author')
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
               validators=(validate_patch_monitoring_data,),
               permission='edit_monitoring')
    def patch(self):
        monitoring = self.request.validated['monitoring']
        monitoring_old_status = monitoring.status

        apply_patch(self.request, save=False, src=self.request.validated['monitoring_src'])

        now = get_now()
        if monitoring_old_status == DRAFT_STATUS and monitoring.status == ACTIVE_STATUS:
            set_author(monitoring.decision.documents, self.request, 'author')
            accelerator = get_monitoring_accelerator(self.context)
            monitoring.monitoringPeriod = generate_period(now, MONITORING_TIME, accelerator)
            monitoring.decision.datePublished = now
            monitoring.endDate = calculate_normalized_business_date(now, MONITORING_TIME, accelerator, True)
        elif monitoring_old_status == ACTIVE_STATUS and monitoring.status == ADDRESSED_STATUS:
            set_author(monitoring.conclusion.documents, self.request, 'author')
            accelerator = get_monitoring_accelerator(self.context)
            monitoring.conclusion.datePublished = now
            monitoring.eliminationPeriod = generate_period(now, ELIMINATION_PERIOD_TIME, accelerator)
        elif monitoring_old_status == ACTIVE_STATUS and monitoring.status == DECLINED_STATUS:
            accelerator = get_monitoring_accelerator(self.context)
            monitoring.eliminationPeriod = generate_period(now, ELIMINATION_PERIOD_NO_VIOLATIONS_TIME, accelerator)
            monitoring.conclusion.datePublished = now
        elif any([
            monitoring_old_status == DRAFT_STATUS and monitoring.status == CANCELLED_STATUS,
            monitoring_old_status == ACTIVE_STATUS and monitoring.status == STOPPED_STATUS,
            monitoring_old_status == DECLINED_STATUS and monitoring.status == STOPPED_STATUS,
            monitoring_old_status == ADDRESSED_STATUS and monitoring.status == STOPPED_STATUS
        ]):
            set_author(monitoring.cancellation.documents, self.request, 'author')
            monitoring.cancellation.datePublished = now

        if monitoring.eliminationResolution:
            monitoring.eliminationResolution.datePublished = monitoring.eliminationResolution.dateCreated

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
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'monitoring_generate_credentials'}))
            return {
                'data': monitoring.serialize('view'),
                'access': {
                    'token': monitoring.tender_owner_token
                }
            }


@op_resource(name='Monitoring count', path='/monitorings/count')
class MonitoringCountResource(APIResource):

    def __init__(self, request, context):
        super(MonitoringCountResource, self).__init__(request, context)
        self.views = {
            "": monitorings_real_count_view,
            "test": monitorings_test_count_view,
        }

    @json_view(permission='view_listing')
    def get(self):
        mode = self.request.params.get('mode', '')
        eval_view = self.views.get(mode, monitorings_real_count_view)
        result = list(eval_view(self.db))
        data = {
            'data': result[0].value if len(result) else 0,
        }
        return data
