from logging import getLogger
from cornice.resource import resource
from functools import partial
from openprocurement.audit.api.constants import SAS_ROLE, PUBLIC_ROLE
from openprocurement.audit.api.utils import (
    get_revision_changes,
    apply_data_patch,
    error_handler,
    update_logging_context,
    context_unpack,
    handle_store_exceptions,
)
from openprocurement.audit.api.context import get_now
from openprocurement.audit.request.models import Request
from openprocurement.audit.request.traversal import factory
from openprocurement.audit.monitoring.utils import (
    add_revision,
)

LOGGER = getLogger(__package__)


op_resource = partial(resource, error_handler=error_handler, factory=factory)


def save_request(request, modified: bool = True, insert=False) -> bool:
    obj = request.validated["request"]
    patch = get_revision_changes(
        request.validated["request_src"], obj.serialize("plain")
    )
    if patch:
        add_revision(request, obj, patch)
        old_date_modified = obj.dateModified
        with handle_store_exceptions(request):
            request.registry.mongodb.request.save(
                obj,
                insert=insert,
                modified=modified,
            )
            LOGGER.info(
                "Saved request {}: dateModified {} -> {}".format(
                    obj.id,
                    old_date_modified and old_date_modified.isoformat(),
                    obj.dateModified.isoformat(),
                ),
                extra=context_unpack(request, {"MESSAGE_ID": "save_request"}),
            )
            return True
    return False


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated["data"] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_request(request)


def generate_request_id(request):
    ctime = get_now().date()
    index_key = "requests_{}".format(ctime.isoformat())
    index = request.registry.mongodb.get_next_sequence_value(index_key)
    return 'UA-R-{:04}-{:02}-{:02}-{:06}'.format(ctime.year, ctime.month, ctime.day, index)


def set_logging_context(event):
    request = event.request
    params = {}
    if "request" in request.validated:
        params["REQUEST_REV"] = request.validated["request"].rev
        params["REQUEST_ID"] = request.validated["request"].id
    update_logging_context(request, params)


def extract_request(request):
    key = "request_id"
    uid = request.matchdict.get(key)
    if uid:
        doc = request.registry.mongodb.request.get(uid)
        if doc is None or doc.get("doc_type") != "Request":
            request.errors.add("url", key, "Not Found")
            request.errors.status = 404
            raise error_handler(request)

        return request.request_from_data(doc)


def request_serialize(request, data, fields):
    obj = request.request_from_data(data, raise_error=False)
    obj.__parent__ = request.context
    return {i: j for i, j in request_serialize_view(
        obj, request.authenticated_role
    ).items() if i in fields}

def request_serialize_view(obj, authenticated_role):
    if authenticated_role in (SAS_ROLE, PUBLIC_ROLE):
        return obj.serialize("view_%s" % authenticated_role)
    else:
        return obj.serialize("view")

def request_from_data(request, data, **_):
    return Request(data)


def set_author(data, request, fieldname='author'):
    for item in data if isinstance(data, list) else [data]:
        setattr(item, fieldname, get_request_role(request.authenticated_role))


def get_request_role(role):
    return 'monitoring_owner' if role == 'sas' else 'request_owner'
