from logging import getLogger
from openprocurement.audit.api.utils import forbidden
from openprocurement.audit.api.views.base import (
    APIResource,
    MongodbResourceListing,
    json_view,
)
from openprocurement.audit.api.utils import (
    context_unpack,
    generate_id,
)
from openprocurement.audit.api.context import get_now
from openprocurement.audit.monitoring.utils import upload_objects_documents
from openprocurement.audit.request.utils import save_request
from openprocurement.audit.request.utils import (
    apply_patch,
    generate_request_id,
    op_resource,
    set_author,
    request_serialize_view,
)
from openprocurement.audit.request.validation import (
    validate_request_data,
    validate_patch_request_data,
)

LOGGER = getLogger(__name__)


@op_resource(name="Requests", path="/requests")
class RequestsResource(MongodbResourceListing):
    def __init__(self, request, context):
        super(RequestsResource, self).__init__(request, context)
        self.listing_name = "Requests"
        self.listing_default_fields = {"dateModified"}
        self.listing_allowed_fields = {
            "dateCreated",
            "dateModified",
            "requestId",
            "description",
            "violationType",
            "answer",
            "dateAnswered",
        }
        self.db_listing_method = request.registry.mongodb.request.list

    @staticmethod
    def add_mode_filters(filters: dict, mode: str):
        if mode == "answered":
            filters["is_answered"] = True
        elif mode == "not_answered":
            filters["is_answered"] = False

        if "test" in mode:
            filters["is_test"] = True
        elif "all" not in mode:
            filters["is_test"] = False

    @json_view(
        content_type="application/json",
        permission="create_request",
        validators=(validate_request_data,),
    )
    def post(self):
        obj = self.request.validated["request"]
        obj.id = generate_id()
        obj.requestId = generate_request_id(self.request)
        set_author(obj.documents, self.request, "author")
        upload_objects_documents(self.request, obj)
        save_request(
            self.request,
            modified=True,
            insert=True
        )
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
        save_request(self.request)
        LOGGER.info(
            "Updated request {}".format(obj.id),
            extra=context_unpack(self.request, {"MESSAGE_ID": "request_patch"}),
        )
        return {"data": request_serialize_view(obj, self.request.authenticated_role)}
