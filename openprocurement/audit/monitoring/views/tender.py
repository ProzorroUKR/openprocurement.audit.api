from logging import getLogger

from pyramid.security import ACLAllowed

from openprocurement.audit.api.utils import (
    context_unpack,
    forbidden,
    json_view,
    APIResourcePaginatedListing,
)
from openprocurement.audit.monitoring.design import (
    MONITORINGS_BY_TENDER_FIELDS,
    monitorings_real_by_tender_id_view,
    monitorings_test_by_tender_id_view,
    monitorings_draft_by_tender_id_view,
    monitorings_real_by_tender_id_total_view,
    monitorings_test_by_tender_id_total_view,
    monitorings_draft_by_tender_id_total_view,
)
from openprocurement.audit.monitoring.utils import monitoring_serialize, op_resource

LOGGER = getLogger(__name__)


@op_resource(name='Tender Monitorings', path='/tenders/{tender_id}/monitorings')
class TenderMonitoringResource(APIResourcePaginatedListing):
    obj_id_key = "tender_id"
    serialize_method = monitoring_serialize
    default_fields = set(MONITORINGS_BY_TENDER_FIELDS) | {"id", "dateCreated"}
    views = {
        "": monitorings_real_by_tender_id_view,
        "test": monitorings_test_by_tender_id_view,
        "draft": monitorings_draft_by_tender_id_view,
    }
    views_total = {
        "": monitorings_real_by_tender_id_total_view,
        "test": monitorings_test_by_tender_id_total_view,
        "draft": monitorings_draft_by_tender_id_total_view,
    }

    @json_view(permission='view_listing')
    def get(self):
        if self.request.params.get('mode') == 'draft':
            perm = self.request.has_permission('view_draft_monitoring')
            if not isinstance(perm, ACLAllowed):
                return forbidden(self.request)
        return super(TenderMonitoringResource, self).get()
