from logging import getLogger

from cornice.resource import resource
from couchdb import ResourceConflict
from functools import partial
from gevent import sleep
from schematics.exceptions import ModelValidationError

from openprocurement.audit.api.utils import (
    get_revision_changes,
    apply_data_patch, error_handler, get_now,
    update_logging_context, context_unpack
)
from openprocurement.audit.inspection.models import Inspection
from openprocurement.audit.inspection.traversal import factory
from openprocurement.audit.monitoring.utils import (
    add_revision,
)

LOGGER = getLogger(__package__)


op_resource = partial(resource, error_handler=error_handler, factory=factory)


def save_inspection(request, date_modified=None):
    inspection = request.validated['inspection']
    patch = get_revision_changes(request.validated['inspection_src'], inspection.serialize("plain"))
    if patch:
        add_revision(request, inspection, patch)

        old_date_modified = inspection.dateModified
        inspection.dateModified = date_modified or get_now()
        try:
            inspection.store(request.registry.db)
        except ModelValidationError as e:  # pragma: no cover
            for i in e.message:
                request.errors.add('body', i, e.message[i])
            request.errors.status = 422
        except Exception as e:  # pragma: no cover
            request.errors.add('body', 'data', str(e))
        else:
            LOGGER.info(
                'Saved inspection {}: dateModified {} -> {}'.format(
                    inspection.id,
                    old_date_modified and old_date_modified.isoformat(),
                    inspection.dateModified.isoformat()
                ),
                extra=context_unpack(request, {'MESSAGE_ID': 'save_inspection'})
            )
            return True


def apply_patch(request, data=None, save=True, src=None, date_modified=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_inspection(request, date_modified=date_modified)


def generate_inspection_id(ctime, db, server_id=''):
    key = ctime.date().isoformat()
    inspection_id_doc = 'inspectionID_' + server_id if server_id else 'inspectionID'
    while True:
        try:
            inspection_id = db.get(inspection_id_doc, {'_id': inspection_id_doc})
            index = inspection_id.get(key, 1)
            inspection_id[key] = index + 1
            db.save(inspection_id)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return 'UA-I-{:04}-{:02}-{:02}-{:06}{}'.format(
        ctime.year, ctime.month, ctime.day, index, server_id and '-' + server_id)


def set_logging_context(event):
    request = event.request
    params = {}
    if 'inspection' in request.validated:
        params['INSPECTION_REV'] = request.validated['inspection'].rev
        params['INSPECTION_ID'] = request.validated['inspection'].id
    update_logging_context(request, params)


def extract_inspection(request):
    key = "inspection_id"
    uid = request.matchdict.get(key)
    if uid:
        db = request.registry.db
        doc = db.get(uid)
        if doc is not None and doc.get('doc_type') == 'inspection':
            request.errors.add('url', key, 'Archived')
            request.errors.status = 410
            raise error_handler(request.errors)
        elif doc is None or doc.get('doc_type') != 'Inspection':
            request.errors.add('url', key, 'Not Found')
            request.errors.status = 404
            raise error_handler(request.errors)

        return request.inspection_from_data(doc)


def inspection_serialize(request, data, fields):
    obj = request.inspection_from_data(data, raise_error=False)
    obj.__parent__ = request.context
    return {i: j for i, j in obj.serialize("view").items() if i in fields}


def inspection_from_data(request, data, **_):
    return Inspection(data)
