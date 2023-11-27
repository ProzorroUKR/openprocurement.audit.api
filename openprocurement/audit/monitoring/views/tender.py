from logging import getLogger
from pyramid.security import ACLAllowed
from openprocurement.audit.api.utils import forbidden
from openprocurement.audit.api.context import get_request
from openprocurement.audit.monitoring.utils import op_resource, monitoring_serialize
from openprocurement.audit.api.views.base import APIResourcePaginatedListing, json_view

LOGGER = getLogger(__name__)


def serialize(data, fields):
    r = monitoring_serialize(get_request(), data, fields)
    return r


@op_resource(name='Tender Monitorings', path='/tenders/{tender_id}/monitorings')
class TenderMonitoringResource(APIResourcePaginatedListing):
    @staticmethod
    def add_mode_filters(filters: dict, mode: str):
        if "draft" not in mode:
            filters["is_public"] = True
        if mode == "test":
            filters["is_test"] = True
        elif "all" not in mode:
            filters["is_test"] = False

    def __init__(self, request, context):
        super(TenderMonitoringResource, self).__init__(request, context)
        self.db_listing_method = request.registry.mongodb.monitoring.paging_list
        self.default_fields = {"id", "is_masked", "dateCreated", "dateModified", "status"}
        self.serialize_method = serialize
        self.obj_id_key = "tender_id"
        self.obj_id_key_filter = "tender_id"

    @json_view(permission='view_listing')
    def get(self):
        if 'draft' in self.request.params.get('mode', ''):
            perm = self.request.has_permission('view_draft_monitoring')
            if not isinstance(perm, ACLAllowed):
                return forbidden(self.request)
        return super(TenderMonitoringResource, self).get()
