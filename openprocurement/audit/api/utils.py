import decimal
import json
import pytz
from base64 import b64encode, b64decode
from binascii import hexlify, unhexlify
from email.header import decode_header
from json import dumps
from urllib.parse import quote, unquote, urlencode
from urllib.parse import urlparse, urlunsplit, parse_qsl
from nacl.exceptions import BadSignatureError
from nacl.encoding import HexEncoder
from Crypto.Cipher import AES
from cornice.util import json_error
from ciso8601 import parse_datetime
from jsonpatch import make_patch, apply_patch as _apply_patch
from time import time as ttime
from contextlib import contextmanager
from uuid import uuid4
from webob.multidict import NestedMultiDict
from pymongo.errors import DuplicateKeyError
from jsonpointer import resolve_pointer
from openprocurement.audit.api.constants import (
    DOCUMENT_BLACKLISTED_FIELDS,
    DOCUMENT_WHITELISTED_FIELDS,
    ROUTE_PREFIX, SESSION,
    LOGGER, JOURNAL_PREFIX
)
from schematics.exceptions import ModelValidationError
from openprocurement.audit.api.rfc6266 import build_header
from openprocurement.audit.api.events import ErrorDesctiptorEvent
from openprocurement.audit.api.interfaces import IContentConfigurator
from openprocurement.audit.api.interfaces import IOPContent
from openprocurement.audit.api.database import MongodbResourceConflict


def set_parent(item, parent):
    if hasattr(item, '__parent__') and item.__parent__ is None:
        item.__parent__ = parent


def get_root(item):
    """ traverse back to root op content object (plan, tender, contract, etc.)
    """
    while not IOPContent.providedBy(item):
        item = item.__parent__
    return item


def generate_id():
    return uuid4().hex


def get_filename(data):
    try:
        pairs = decode_header(data.filename)
    except Exception:
        pairs = None
    if not pairs:
        return data.filename
    header = pairs[0]
    if header[1]:
        return header[0].decode(header[1])
    else:
        return header[0]


def generate_docservice_url(request, doc_id, temporary=True, prefix=None):
    docservice_key = getattr(request.registry, 'docservice_key', None)
    parsed_url = urlparse(request.registry.docservice_url)
    query = {}
    if temporary:
        expires = int(ttime()) + 300  # EXPIRES
        mess = "{}\0{}".format(doc_id, expires)
        query['Expires'] = expires
    else:
        mess = doc_id
    if prefix:
        mess = '{}/{}'.format(prefix, mess)
        query['Prefix'] = prefix
    signature = docservice_key.sign(mess.encode()).signature
    query['Signature'] = quote(b64encode(signature))
    query['KeyID'] = docservice_key.verify_key.encode(encoder=HexEncoder)[:8].decode()
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, '/get/{}'.format(doc_id), urlencode(query), ''))


def error_handler(request, request_params=True):
    errors = request.errors
    params = {"ERROR_STATUS": errors.status}
    if request_params:
        params["ROLE"] = str(request.authenticated_role)
        if request.params:
            params["PARAMS"] = str(dict(request.params))
    if request.matchdict:
        for x, j in request.matchdict.items():
            params[x.upper()] = j
    request.registry.notify(ErrorDesctiptorEvent(request, params))

    for item in errors:
        for key, value in item.items():
            if isinstance(value, bytes):
                item[key] = value.decode("utf-8")

    LOGGER.info(
        'Error on processing request "{}"'.format(dumps(errors, indent=4)),
        extra=context_unpack(request, {"MESSAGE_ID": "error_handler"}, params),
    )
    return json_error(request)


def raise_operation_error(request, message, status=403, location='body', name='data'):
    """
    This function mostly used in views validators to add access errors and
    raise exceptions if requested operation is forbidden.
    """
    request.errors.add(location, name, message)
    request.errors.status = status
    raise error_handler(request)


def upload_file(request,
                blacklisted_fields=DOCUMENT_BLACKLISTED_FIELDS,
                whitelisted_fields=DOCUMENT_WHITELISTED_FIELDS):
    first_document = request.validated['documents'][-1] if 'documents' in request.validated and request.validated['documents'] else None
    if 'data' in request.validated and request.validated['data']:
        document = request.validated['document']
        check_document(request, document, 'body')

        if first_document:
            for attr_name in type(first_document)._fields:
                if attr_name in whitelisted_fields:
                    setattr(document, attr_name, getattr(first_document, attr_name))
                elif attr_name not in blacklisted_fields and attr_name not in request.validated['json_data']:
                    setattr(document, attr_name, getattr(first_document, attr_name))

        document_route = request.matched_route.name.replace("collection_", "")
        document = update_document_url(request, document, document_route, {})
        return document
    if request.content_type == 'multipart/form-data':
        data = request.validated['file']
        filename = get_filename(data)
        content_type = data.type
        in_file = data.file
    else:
        filename = first_document.title
        content_type = request.content_type
        in_file = request.body_file

    if hasattr(request.context, "documents"):
        # upload new document
        model = type(request.context).documents.model_class
    else:
        # update document
        model = type(request.context)
    document = model({'title': filename, 'format': content_type})
    document.__parent__ = request.context
    if 'document_id' in request.validated:
        document.id = request.validated['document_id']
    if first_document:
        for attr_name in type(first_document)._fields:
            if attr_name not in blacklisted_fields:
                setattr(document, attr_name, getattr(first_document, attr_name))
    if request.registry.docservice_url:
        parsed_url = urlparse(request.registry.docservice_url)
        url = request.registry.docservice_upload_url or urlunsplit((parsed_url.scheme, parsed_url.netloc, '/upload', '', ''))
        files = {'file': (filename, in_file, content_type)}
        doc_url = None
        index = 10
        while index:
            try:
                r = SESSION.post(
                    url,
                    files=files,
                    headers={'X-Client-Request-ID': request.environ.get('REQUEST_ID', '')},
                    auth=(request.registry.docservice_username, request.registry.docservice_password))
                json_data = r.json()
            except Exception as e:
                LOGGER.warning(
                    "Raised exception '{}' on uploading document "
                    "to document service': {}.".format(type(e), e),
                    extra=context_unpack(
                        request, {'MESSAGE_ID': 'document_service_exception'},
                        {'file_size': in_file.tell()}))
            else:
                if r.status_code == 200 and json_data.get('data', {}).get('url'):
                    doc_url = json_data['data']['url']
                    doc_hash = json_data['data']['hash']
                    break
                else:
                    LOGGER.warning(
                        "Error {} on uploading document "
                        "to document service '{}': {}".format(r.status_code, url, r.text),
                        extra=context_unpack(
                            request, {'MESSAGE_ID': 'document_service_error'},
                            {'ERROR_STATUS': r.status_code, 'file_size': in_file.tell()}))
            in_file.seek(0)
            index -= 1
        else:
            request.errors.add('body', 'data', "Can't upload document to document service.")
            request.errors.status = 422
            raise error_handler(request)
        document.hash = doc_hash
        key = urlparse(doc_url).path.split('/')[-1]
    else:
        key = generate_id()
        filename = "{}_{}".format(document.id, key)
        request.validated['db_doc']['_attachments'][filename] = {
            "content_type": document.format,
            "data": b64encode(in_file.read())}
    document_route = request.matched_route.name.replace("collection_", "")
    document_path = request.current_route_path(
        _route_name=document_route,
        document_id=document.id,
        _query={'download': key})
    document.url = '/' + '/'.join(document_path.split('/')[3:])
    update_logging_context(request, {'file_size': in_file.tell()})
    return document


def update_file_content_type(request):  # XXX TODO
    pass


def get_file(request):
    db_doc = request.validated['db_doc']
    db_doc_id = db_doc.id
    document = request.validated['document']
    key = request.params.get('download')
    if not any([key in i.url for i in request.validated['documents']]):
        request.errors.add('url', 'download', 'Not Found')
        request.errors.status = 404
        return
    document = [i for i in request.validated['documents'] if key in i.url][-1]
    if 'Signature=' in document.url and 'KeyID' in document.url:
        url = document.url
    else:
        if 'download=' not in document.url:
            key = urlparse(document.url).path.replace('/get/', '')
        if not document.hash:
            url = generate_docservice_url(request, key, prefix='{}/{}'.format(db_doc_id, document.id))
        else:
            url = generate_docservice_url(request, key)
    request.response.content_type = document.format
    request.response.content_disposition = build_header(
        document.title, filename_compat=quote(document.title)
    ).decode("utf-8")
    request.response.status = '302 Moved Temporarily'
    request.response.location = url
    return url


def prepare_patch(changes, orig, patch, basepath=''):
    if isinstance(patch, dict):
        for i in patch:
            if i in orig:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': patch[i]})
    elif isinstance(patch, list):
        if len(patch) < len(orig):
            for i in reversed(range(len(patch), len(orig))):
                changes.append({'op': 'remove', 'path': '{}/{}'.format(basepath, i)})
        for i, j in enumerate(patch):
            if len(orig) > i:
                prepare_patch(changes, orig[i], patch[i], '{}/{}'.format(basepath, i))
            else:
                changes.append({'op': 'add', 'path': '{}/{}'.format(basepath, i), 'value': j})
    else:
        for x in make_patch(orig, patch).patch:
            x['path'] = '{}{}'.format(basepath, x['path'])
            changes.append(x)


def apply_data_patch(item, changes):
    patch_changes = []
    prepare_patch(patch_changes, item, changes)
    if not patch_changes:
        return {}
    return _apply_patch(item, patch_changes)


def get_revision_changes(dst, src):
    return make_patch(dst, src).patch


def set_ownership(data, request, fieldname='owner', token=True):
    for item in data if isinstance(data, list) else [data]:
        setattr(item, fieldname, request.authenticated_userid)
        if token:
            setattr(item, '{}_token'.format(fieldname), generate_id())


def check_document(request, document, document_container):
    url = document.url
    parsed_url = urlparse(url)
    parsed_query = dict(parse_qsl(parsed_url.query))
    if not url.startswith(request.registry.docservice_url) or \
            len(parsed_url.path.split('/')) != 3 or \
            set(['Signature', 'KeyID']) != set(parsed_query):
        request.errors.add(document_container, 'url', "Can add document only from document service.")
        request.errors.status = 403
        raise error_handler(request)
    if not document.hash:
        request.errors.add(document_container, 'hash', "This field is required.")
        request.errors.status = 422
        raise error_handler(request)
    keyid = parsed_query['KeyID']
    if keyid not in request.registry.keyring:
        request.errors.add(document_container, 'url', "Document url expired.")
        request.errors.status = 422
        raise error_handler(request)
    dockey = request.registry.keyring[keyid]
    signature = parsed_query['Signature']
    key = urlparse(url).path.split('/')[-1]
    try:
        signature = b64decode(unquote(signature))
    except TypeError:
        request.errors.add(document_container, 'url', "Document url signature invalid.")
        request.errors.status = 422
        raise error_handler(request)
    mess = "{}\0{}".format(key, document.hash.split(':', 1)[-1])
    try:
        dockey.verify(mess.encode("utf-8"), signature)
    except BadSignatureError:
        request.errors.add(document_container, 'url', "Document url invalid.")
        request.errors.status = 422
        raise error_handler(request)


def update_document_url(request, document, document_route, route_kwargs):
    key = urlparse(document.url).path.split('/')[-1]
    route_kwargs.update({'_route_name': document_route,
                         'document_id': document.id,
                         '_query': {'download': key}})
    document_path = request.current_route_path(**route_kwargs)
    document.url = '/' + '/'.join(document_path.split('/')[3:])
    return document


def check_document_batch(request, document, document_container, route_kwargs):
    check_document(request, document, document_container)

    document_route = request.matched_route.name.replace("collection_", "")
    # Following piece of code was written by leits, so no one knows how it works
    # and why =)
    # To redefine document_route to get appropriate real document route when bid
    # is created with documents? I hope so :)
    if "Documents" not in document_route:
        specified_document_route_end = (
            document_container.lower().rsplit('documents')[0] + ' documents'
        ).lstrip().title()
        document_route = ' '.join([document_route[:-1], specified_document_route_end])

    return update_document_url(request, document, document_route, route_kwargs)


def append_tender_revision(request, tender, patch, date):
    status_changes = [p for p in patch if all([
        not p["path"].startswith("/bids/"),
        p["path"].endswith("/status"),
        p["op"] == "replace"
    ])]
    for change in status_changes:
        obj = resolve_pointer(tender, change["path"].replace("/status", ""))
        if obj and hasattr(obj, "date"):
            date_path = change["path"].replace("/status", "/date")
            if obj.date and not any([p for p in patch if date_path == p["path"]]):
                patch.append({"op": "replace", "path": date_path, "value": obj.date.isoformat()})
            elif not obj.date:
                patch.append({"op": "remove", "path": date_path})
            obj.date = date
    return append_revision(request, tender, patch)


def append_revision(request, obj, patch):
    revision_data = {
        "author": request.authenticated_userid,
        "changes": patch,
        "rev": obj.rev
    }
    from openprocurement.audit.api.models import Revision
    obj.revisions.append(Revision(revision_data))
    return obj.revisions


@contextmanager
def handle_store_exceptions(request):
    try:
        yield
    except ModelValidationError as e:
        for i in e.messages:
            request.errors.add("body", i, e.messages[i])
        request.errors.status = 422
    except MongodbResourceConflict as e:  # pragma: no cover
        request.errors.add("body", "data", str(e))
        request.errors.status = 409
    except DuplicateKeyError as e:  # pragma: no cover
        request.errors.add("body", "data", "Document already exists")
        request.errors.status = 409
    except Exception as e:  # pragma: no cover
        LOGGER.exception(e)
        request.errors.add("body", "data", str(e))


def request_params(request):
    try:
        params = NestedMultiDict(request.GET, request.POST)
    except UnicodeDecodeError:
        request.errors.add('body', 'data', 'could not decode params')
        request.errors.status = 422
        raise error_handler(request, False)
    except Exception as e:
        request.errors.add('body', str(e.__class__.__name__), str(e))
        request.errors.status = 422
        raise error_handler(request, False)
    return params


def parse_date(value, default_timezone=pytz.utc):
    date = parse_datetime(value)
    if not date.tzinfo:
        date = default_timezone.localize(date)
    return date


def parse_offset(offset: str):
    try:
        # Used new offset in timestamp format
        return float(offset)
    except ValueError:
        # Used deprecated offset in iso format
        return parse_date(offset.replace(" ", "+")).timestamp()


def forbidden(request):
    request.errors.add('url', 'permission', 'Forbidden')
    request.errors.status = 403
    return error_handler(request)


def update_logging_context(request, params):
    if not request.__dict__.get('logging_context'):
        request.logging_context = {}

    for x, j in params.items():
        request.logging_context[x.upper()] = j


def context_unpack(request, msg, params=None):
    if params:
        update_logging_context(request, params)
    logging_context = request.logging_context
    journal_context = msg
    for key, value in logging_context.items():
        journal_context[JOURNAL_PREFIX + key] = value
    return journal_context


def get_content_configurator(request):
    content_type = request.path[len(ROUTE_PREFIX)+1:].split('/')[0][:-1]
    if hasattr(request, content_type):  # content is constructed
        context = getattr(request, content_type)
        return request.registry.queryMultiAdapter((context, request), IContentConfigurator)


def fix_url(item, app_url):
    if isinstance(item, list):
        [
            fix_url(i, app_url)
            for i in item
            if isinstance(i, dict) or isinstance(i, list)
        ]
    elif isinstance(item, dict):
        if "format" in item and "url" in item and '?download=' in item['url']:
            path = item["url"] if item["url"].startswith('/') else '/' + '/'.join(item['url'].split('/')[5:])
            item["url"] = app_url + ROUTE_PREFIX + path
            return [
                fix_url(item[i], app_url)
                for i in item
                if isinstance(item[i], dict) or isinstance(item[i], list)
            ]


def encrypt(uuid, name, key):
    iv = "{:^{}.{}}".format(name, AES.block_size, AES.block_size)
    text = "{:^{}}".format(key, AES.block_size)
    return hexlify(AES.new(uuid, AES.MODE_CBC, iv).encrypt(text))


def decrypt(uuid, name, key):
    iv = "{:^{}.{}}".format(name, AES.block_size, AES.block_size)
    try:
        text = AES.new(uuid, AES.MODE_CBC, iv).decrypt(unhexlify(key)).strip()
    except:
        text = ''
    return text


def set_modetest_titles(item):
    if not item.title or u'[ТЕСТУВАННЯ]' not in item.title:
        item.title = u'[ТЕСТУВАННЯ] {}'.format(item.title or u'')
    if not item.title_en or u'[TESTING]' not in item.title_en:
        item.title_en = u'[TESTING] {}'.format(item.title_en or u'')
    if not item.title_ru or u'[ТЕСТИРОВАНИЕ]' not in item.title_ru:
        item.title_ru = u'[ТЕСТИРОВАНИЕ] {}'.format(item.title_ru or u'')


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


def get_first_revision_date(schematics_document, default=None):
    revisions = schematics_document.get('revisions')
    return revisions[0].date if revisions else default
