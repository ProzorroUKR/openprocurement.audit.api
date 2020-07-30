from logging import getLogger
from openprocurement.audit.api.utils import json_view
from openprocurement.audit.inspection.views.inspection import InspectionsResource
from openprocurement.audit.inspection.utils import op_resource

LOGGER = getLogger(__name__)


@op_resource(name='Monitoring inspections',
             path='/monitorings/{monitoring_id}/inspections')
class MonitoringInspectionsResource(InspectionsResource):
    listing_default_fields = {"id", "dateModified",
                              "dateCreated", "inspection_id"}
    listing_safe_fields = {"id", "dateModified", "dateCreated",
                           "inspection_id"}

    @json_view(permission='view_listing')
    def get(self):
        monitoring_id = self.request.matchdict["monitoring_id"]
        self.listing_filters = {"monitoring_ids": monitoring_id}
        return super(MonitoringInspectionsResource, self).get()
