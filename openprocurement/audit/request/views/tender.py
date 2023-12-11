from logging import getLogger
from openprocurement.audit.api.views.base import APIResourcePaginatedListing
from openprocurement.audit.request.utils import request_serialize, op_resource
from openprocurement.audit.api.context import get_request

LOGGER = getLogger(__name__)


def serialize(data, fields):
    r = request_serialize(get_request(), data, fields)
    return r


@op_resource(name='Tender Requests', path='/tenders/{tender_id}/requests')
class TenderRequestResource(APIResourcePaginatedListing):
    def __init__(self, request, context):
        super(TenderRequestResource, self).__init__(request, context)
        self.db_listing_method = request.registry.mongodb.request.paging_list
        self.default_fields = {
            "id",
            "dateCreated",
            "dateModified",
            "requestId",
            "description",
            "violationType",
            "answer",
            "dateAnswered",
            "dateCreated",
        }
        self.serialize_method = serialize
        self.obj_id_key = "tender_id"
        self.obj_id_key_filter = "tenderId"
