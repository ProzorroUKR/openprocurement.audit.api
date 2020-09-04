from logging import getLogger

from openprocurement.audit.api.utils import APIResourcePaginatedListing
from openprocurement.audit.inspection.design import (
    CHANGES_FIELDS,
    inspections_real_by_monitoring_id_view,
    inspections_real_by_monitoring_id_total_view,
)
from openprocurement.audit.inspection.utils import (
    inspection_serialize,
    op_resource,
)

LOGGER = getLogger(__name__)


@op_resource(name='Monitoring inspections', path='/monitorings/{monitoring_id}/inspections')
class MonitoringInspectionsResource(APIResourcePaginatedListing):
    obj_id_key = "monitoring_id"
    serialize_method = inspection_serialize
    default_fields = set(CHANGES_FIELDS) | {"id", "dateCreated"}
    views = {
        "": inspections_real_by_monitoring_id_view,
    }
    views_total = {
        "": inspections_real_by_monitoring_id_total_view,
    }
