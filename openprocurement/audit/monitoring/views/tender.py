from logging import getLogger
from pyramid.security import ACLAllowed
from openprocurement.audit.api.utils import forbidden, json_view
from openprocurement.audit.monitoring.utils import op_resource
from openprocurement.audit.monitoring.views.monitoring import MonitoringsResource

LOGGER = getLogger(__name__)


@op_resource(name='Tender Monitorings', path='/tenders/{tender_id}/monitorings')
class TenderMonitoringResource(MonitoringsResource):
    listing_default_fields = {"id", "status", "dateCreated"}
    listing_safe_fields = {"id", "status", "dateCreated"}

    @json_view(permission='view_listing')
    def get(self):
        if 'draft' in self.request.params.get('mode', ''):
            perm = self.request.has_permission('view_draft_monitoring')
            if not isinstance(perm, ACLAllowed):
                return forbidden(self.request)

        tender_id = self.request.matchdict["tender_id"]
        self.listing_filters = {"tender_id": tender_id}
        return super(TenderMonitoringResource, self).get()
