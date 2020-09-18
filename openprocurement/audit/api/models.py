from string import hexdigits
from urllib.parse import parse_qs, urlparse

from schematics.types.serializable import serializable
from uuid import uuid4

from couchdb_schematics.document import DocumentMeta, Document as SchematicsDocument
from schematics.models import Model as SchematicsModel
from schematics.transforms import blacklist, convert, export_loop, whitelist
from schematics.types import BaseType, StringType, MD5Type, URLType, EmailType
from schematics.types.compound import DictType, ModelType
from zope.component import queryAdapter, getAdapters

from openprocurement.audit.api.constants import ORA_CODES
from openprocurement.audit.api.interfaces import IValidator, ISerializable
from openprocurement.audit.api.types import IsoDateTimeType, ListType, HashType
from openprocurement.audit.api.utils import set_parent, get_now

schematics_default_role = SchematicsDocument.Options.roles['default'] + blacklist("__parent__")
schematics_embedded_role = SchematicsDocument.Options.roles['embedded'] + blacklist("__parent__")


class AdaptiveDict(dict):
    def __init__(self, context, interface, data, prefix=''):
        self.context = context
        self.interface = interface
        self.prefix = prefix
        self.prefix_len = len(prefix)
        self.adaptive_items = {}
        super(AdaptiveDict, self).__init__(data)

    def __contains__(self, item):
        return item in self.keys()

    def __getitem__(self, key):
        if key in self.adaptive_items:
            return self.adaptive_items[key]
        if self.prefix and key.startswith(self.prefix):
            adapter = queryAdapter(self.context, self.interface, key[self.prefix_len:])
        else:
            adapter = queryAdapter(self.context, self.interface, key)
        if adapter:
            return adapter
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def keys(self):
        return list(self)

    def __iter__(self):
        for item in self.iteritems():
            yield item[0]

    def iteritems(self):
        for i in super(AdaptiveDict, self).items():
            yield i
        for k, v in getAdapters((self.context,), self.interface):
            if self.prefix:
                k = self.prefix + k
            self.adaptive_items[k] = v
        for i in self.adaptive_items.items():
            yield i


class OpenprocurementCouchdbDocumentMeta(DocumentMeta):

    def __new__(mcs, name, bases, attrs):
        klass = DocumentMeta.__new__(mcs, name, bases, attrs)
        klass._validator_functions = AdaptiveDict(
            klass,
            IValidator,
            klass._validator_functions
        )
        klass._serializables = AdaptiveDict(
            klass, ISerializable,
            klass._serializables,
        )
        return klass


class Model(SchematicsModel, metaclass=OpenprocurementCouchdbDocumentMeta):

    default_role = 'edit'

    class Options(object):
        """Export options for Document."""
        serialize_when_none = False
        roles = {
            "default": blacklist("__parent__"),
            "embedded": blacklist("__parent__"),
        }

    __parent__ = BaseType()

    def __getattribute__(self, name):
        serializables = super(Model, self).__getattribute__('_serializables')
        if name in serializables.adaptive_items:
            return serializables[name](self)
        return super(Model, self).__getattribute__(name)

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError as e:
            raise KeyError(e.args[0])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for k in self._fields:
                if k != '__parent__' and self.get(k) != other.get(k):
                    return False
            return True
        return NotImplemented

    def convert(self, raw_data, **kw):
        """
        Converts the raw data into richer Python constructs according to the
        fields on the model
        """
        value = convert(self.__class__, raw_data, **kw)
        for i, j in value.items():
            if isinstance(j, list):
                for x in j:
                    set_parent(x, self)
            else:
                set_parent(j, self)
        return value

    def to_patch(self, role=None):
        """
        Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        field_converter = lambda field, value: field.to_primitive(value)
        data = export_loop(self.__class__, self, field_converter, role=role, raise_error_on_role=True, print_none=True)
        return data

    def get_role(self):
        return self.default_role


class Revision(Model):
    author = StringType()
    date = IsoDateTimeType(default=get_now)
    changes = ListType(DictType(BaseType), default=list())
    rev = StringType()


class Document(Model):
    class Options:
        roles = {
            'create': blacklist('id', 'datePublished', 'dateModified', 'author', 'download_url'),
            'edit': blacklist('id', 'url', 'datePublished', 'dateModified', 'author', 'hash', 'download_url'),
            'embedded': (blacklist('url', 'download_url') + schematics_embedded_role),
            'default': blacklist("__parent__"),
            'view': (blacklist('revisions') + schematics_default_role),
            'revisions': whitelist('url', 'dateModified'),
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    hash = HashType()
    title = StringType(required=True)  # A title of the document.
    title_en = StringType()
    title_ru = StringType()
    description = StringType()  # A description of the document.
    description_en = StringType()
    description_ru = StringType()
    format = StringType(required=True, regex='^[-\w]+/[-\.\w\+]+$')
    url = StringType(required=True)  # Link to the document or attachment.
    datePublished = IsoDateTimeType(default=get_now)
    dateModified = IsoDateTimeType(default=get_now)  # Date that the document was last dateModified
    language = StringType()
    relatedItem = MD5Type()
    author = StringType()
    documentType = StringType(
        choices=[
            "tenderNotice",
            "awardNotice",
            "contractNotice",
            "notice",
            "biddingDocuments",
            "technicalSpecifications",
            "evaluationCriteria",
            "clarifications",
            "shortlistedFirms",
            "riskProvisions",
            "billOfQuantity",
            "bidders",
            "conflictOfInterest",
            "debarments",
            "evaluationReports",
            "winningBid",
            "complaints",
            "contractSigned",
            "contractArrangements",
            "contractSchedule",
            "contractAnnexe",
            "contractGuarantees",
            "subContract",
            "eligibilityCriteria",
            "contractProforma",
            "commercialProposal",
            "qualificationDocuments",
            "eligibilityDocuments",
            "registerExtract",
            "registerFiscal",
        ]
    )

    @serializable(serialized_name="url")
    def download_url(self):
        url = self.url
        if not url or '?download=' not in url:
            return url
        doc_id = parse_qs(urlparse(url).query)['download'][-1]
        root = self.__parent__
        parents = []
        while root.__parent__ is not None:
            parents[0:0] = [root]
            root = root.__parent__
        request = root.request
        if not request.registry.docservice_url:
            return url
        if 'status' in parents[0] and parents[0].status in type(parents[0])._options.roles:
            role = parents[0].status
            for index, obj in enumerate(parents):
                if obj.id != url.split('/')[(index - len(parents)) * 2 - 1]:
                    break
                field = url.split('/')[(index - len(parents)) * 2]
                if "_" in field:
                    field = field[0] + field.title().replace("_", "")[1:]
                roles = type(obj)._options.roles
                if roles[role if role in roles else 'default'](field, []):
                    return url
        from openprocurement.audit.api.utils import generate_docservice_url
        if not self.hash:
            path = [i for i in urlparse(url).path.split('/') if len(i) == 32 and not set(i).difference(hexdigits)]
            return generate_docservice_url(request, doc_id, False, '{}/{}'.format(path[0], path[-1]))
        return generate_docservice_url(request, doc_id, False)

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if data[k] == getattr(self, k)]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self


class BaseModel(SchematicsDocument, Model):

    @serializable(serialized_name='id')
    def doc_id(self):
        """
        A property that is serialized by schematics exports.
        """
        return self._id

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [
            k for k in data.keys()
            if data[k] == self.__class__.fields[k].default
               or data[k] == getattr(self, k)
        ]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self


class Identifier(Model):
    scheme = StringType(required=True, choices=ORA_CODES)
    id = BaseType(required=True)
    legalName = StringType()
    legalName_en = StringType()
    legalName_ru = StringType()
    uri = URLType()


class Address(Model):
    streetAddress = StringType()
    locality = StringType()
    region = StringType()
    postalCode = StringType()
    countryName = StringType()
    countryName_en = StringType()
    countryName_ru = StringType()


class ContactPoint(Model):
    name = StringType()
    name_en = StringType()
    name_ru = StringType()
    email = EmailType()
    telephone = StringType()
    faxNumber = StringType()
    url = URLType()


class Party(Model):
    id = MD5Type(required=True, default=lambda: uuid4().hex)
    name = StringType(required=True, min_length=1)
    identifier = ModelType(Identifier)
    additionalIdentifiers = ListType(ModelType(Identifier))
    address = ModelType(Address)
    contactPoint = ModelType(ContactPoint)
    roles = ListType(StringType(choices=[]), default=[])
    datePublished = IsoDateTimeType(default=get_now)
