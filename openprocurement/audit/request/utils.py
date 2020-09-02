from logging import getLogger

from cornice.resource import resource
from couchdb import ResourceConflict
from functools import partial
from gevent import sleep
from schematics.exceptions import ModelValidationError

from openprocurement.audit.api.utils import (
    get_revision_changes,
    apply_data_patch,
    error_handler,
    get_now,
    update_logging_context,
    context_unpack,
)
from openprocurement.audit.request.models import Request
from openprocurement.audit.request.traversal import factory
from openprocurement.audit.monitoring.utils import (
    add_revision,
)

LOGGER = getLogger(__package__)


op_resource = partial(resource, error_handler=error_handler, factory=factory)


def save_request(request, date_modified=None):
    obj = request.validated["request"]
    patch = get_revision_changes(
        request.validated["request_src"], obj.serialize("plain")
    )
    if patch:
        add_revision(request, obj, patch)

        old_date_modified = obj.dateModified
        obj.dateModified = date_modified or get_now()
        try:
            obj.store(request.registry.db)
        except ModelValidationError as e:  # pragma: no cover
            for i in e.messages:
                request.errors.add("body", i, e.messages[i])
            request.errors.status = 422
        except Exception as e:  # pragma: no cover
            request.errors.add("body", "data", str(e))
        else:
            LOGGER.info(
                "Saved request {}: dateModified {} -> {}".format(
                    obj.id,
                    old_date_modified and old_date_modified.isoformat(),
                    obj.dateModified.isoformat(),
                ),
                extra=context_unpack(request, {"MESSAGE_ID": "save_request"}),
            )
            return True


def apply_patch(request, data=None, save=True, src=None, date_modified=None):
    data = request.validated["data"] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_request(request, date_modified=date_modified)


def generate_request_id(ctime, db, server_id=""):
    key = ctime.date().isoformat()
    request_id_doc = "requestID_" + server_id if server_id else "requestID"
    while True:
        try:
            request_id = db.get(request_id_doc, {"_id": request_id_doc})
            index = request_id.get(key, 1)
            request_id[key] = index + 1
            db.save(request_id)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return "UA-R-{:04}-{:02}-{:02}-{:06}{}".format(
        ctime.year, ctime.month, ctime.day, index, server_id and "-" + server_id
    )


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
        db = request.registry.db
        doc = db.get(uid)
        if doc is not None and doc.get("doc_type") == "request":
            request.errors.add("url", key, "Archived")
            request.errors.status = 410
            raise error_handler(request.errors)
        elif doc is None or doc.get("doc_type") != "Request":
            request.errors.add("url", key, "Not Found")
            request.errors.status = 404
            raise error_handler(request.errors)

        return request.request_from_data(doc)


def request_serialize(request, data, fields):
    obj = request.request_from_data(data, raise_error=False)
    obj.__parent__ = request.context
    return {i: j for i, j in obj.serialize("view").items() if i in fields}


def request_from_data(request, data, **_):
    return Request(data)


def set_author(data, request, fieldname='author'):
    for item in data if isinstance(data, list) else [data]:
        setattr(item, fieldname, get_request_role(request.authenticated_role))


def get_request_role(role):
    return 'monitoring_owner' if role == 'sas' else 'request_owner'
