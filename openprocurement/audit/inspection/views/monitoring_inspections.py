from openprocurement.audit.inspection.utils import op_resource, inspection_serialize
from openprocurement.audit.api.views.base import APIResourcePaginatedListing
from openprocurement.audit.api.context import get_request


def serialize(data, fields):
    r = inspection_serialize(get_request(), data, fields)
    return r


@op_resource(name='Monitoring inspections',
             path='/monitorings/{monitoring_id}/inspections')
class MonitoringInspectionsResource(APIResourcePaginatedListing):

    def __init__(self, request, context):
        super(MonitoringInspectionsResource, self).__init__(request, context)
        self.db_listing_method = request.registry.mongodb.inspection.paging_list
        self.default_fields = {"id", "dateCreated", "dateModified", "inspection_id"}
        self.serialize_method = serialize
        self.obj_id_key = "monitoring_id"
        self.obj_id_key_filter = "monitoring_ids"
