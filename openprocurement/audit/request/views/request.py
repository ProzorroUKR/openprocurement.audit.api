from logging import getLogger

from openprocurement.audit.api.constants import SAS_ROLE, PUBLIC_ROLE
from openprocurement.audit.api.utils import (
    APIResource,
    APIResourceListing,
    json_view,
    forbidden,
)
from openprocurement.audit.api.utils import (
    context_unpack,
    get_now,
    generate_id,
)
from openprocurement.audit.request.design import (
    FIELDS,
    requests_real_by_dateModified_view,
    requests_real_by_local_seq_view,
    requests_real_answered_by_dateModified_view,
    requests_real_not_answered_by_dateModified_view,
    requests_real_answered_by_local_seq_view,
    requests_real_not_answered_by_local_seq_view,
)
from openprocurement.audit.request.utils import (
    save_request,
    apply_patch,
    generate_request_id,
    request_serialize,
    op_resource,
    set_author,
    request_serialize_view,
)
from openprocurement.audit.request.validation import (
    validate_request_data,
    validate_patch_request_data,
)

LOGGER = getLogger(__name__)
VIEW_MAP = {
    u"": requests_real_by_dateModified_view,
    u"answered": requests_real_answered_by_dateModified_view,
    u"not_answered": requests_real_not_answered_by_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u"": requests_real_by_local_seq_view,
    u"answered": requests_real_answered_by_local_seq_view,
    u"not_answered": requests_real_not_answered_by_local_seq_view,
}
FEED = {
    u"dateModified": VIEW_MAP,
    u"changes": CHANGES_VIEW_MAP,
}


@op_resource(name="Requests", path="/requests")
class RequestsResource(APIResourceListing):
    def __init__(self, request, context):
        super(RequestsResource, self).__init__(request, context)

        self.VIEW_MAP = VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = request_serialize
        self.object_name_for_listing = "Requests"
        self.log_message_id = "requests_list_custom"

    @json_view(
        content_type="application/json",
        permission="create_request",
        validators=(validate_request_data,),
    )
    def post(self):
        obj = self.request.validated["request"]
        obj.id = generate_id()
        obj.requestId = generate_request_id(get_now(), self.db, self.server_id)
        set_author(obj.documents, self.request, "author")
        save_request(self.request, date_modified=obj.dateCreated)
        LOGGER.info(
            "Created request {}".format(obj.id),
            extra=context_unpack(
                self.request,
                {"MESSAGE_ID": "request_create"},
                {"MONITORING_ID": obj.id},
            ),
        )
        self.request.response.status = 201
        self.request.response.headers["Location"] = self.request.route_url(
            "Request", request_id=obj.id
        )
        return {"data": request_serialize_view(obj, self.request.authenticated_role)}


@op_resource(name="Request", path="/requests/{request_id}")
class RequestResource(APIResource):
    @json_view(permission="view_request")
    def get(self):
        obj = self.request.validated["request"]
        return {"data": request_serialize_view(obj, self.request.authenticated_role)}

    @json_view(
        content_type="application/json",
        validators=(validate_patch_request_data,),
        permission="edit_request",
    )
    def patch(self):
        obj = self.request.validated["request"]
        now = get_now()
        if obj.answer is not None:
            raise forbidden(self.request)
        apply_patch(self.request, src=self.request.validated["request_src"], save=False)
        if obj.answer:
            obj.dateAnswered = now
        save_request(self.request, date_modified=now)
        LOGGER.info(
            "Updated request {}".format(obj.id),
            extra=context_unpack(self.request, {"MESSAGE_ID": "request_patch"}),
        )
        return {"data": request_serialize_view(obj, self.request.authenticated_role)}
