from logging import getLogger

from openprocurement.audit.api.utils import (
    APIResourcePaginatedListing,
)
from openprocurement.audit.request.design import (
    CHANGES_FIELDS,
    requests_real_by_tender_id_view,
    requests_real_by_tender_id_total_view,
)
from openprocurement.audit.request.utils import request_serialize, op_resource

LOGGER = getLogger(__name__)



@op_resource(name='Tender Requests', path='/tenders/{tender_id}/requests')
class TenderRequestResource(APIResourcePaginatedListing):
    obj_id_key = "tender_id"
    serialize_method = request_serialize
    default_fields = set(CHANGES_FIELDS) | {"id", "dateCreated"}
    views = {
        "": requests_real_by_tender_id_view,
    }
    views_total = {
        "": requests_real_by_tender_id_total_view,
    }
