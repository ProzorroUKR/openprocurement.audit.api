from couchdb_schematics.document import DocumentMeta
from schematics.models import Model as SchematicsModel
from schematics.transforms import blacklist, convert, export_loop
from schematics.types import BaseType
from zope.component import queryAdapter, getAdapters

from openprocurement.audit.api.interfaces import IValidator, ISerializable


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
        adapter = None
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
        for i in super(AdaptiveDict, self).iteritems():
            yield i
        for k, v in getAdapters((self.context,), self.interface):
            if self.prefix:
                k = self.prefix + k
            self.adaptive_items[k] = v
        for i in self.adaptive_items.iteritems():
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


class Model(SchematicsModel):
    __metaclass__ = OpenprocurementCouchdbDocumentMeta

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
            raise KeyError(e.message)

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
                    self.set_parent(x)
            else:
                self.set_parent(j)
        return value

    def to_patch(self, role=None):
        """
        Return data as it would be validated. No filtering of output unless
        role is defined.
        """
        field_converter = lambda field, value: field.to_primitive(value)
        data = export_loop(self.__class__, self, field_converter, role=role, raise_error_on_role=True, print_none=True)
        return data

    def set_parent(self, item):
        if hasattr(item, '__parent__') and item.__parent__ is None:
            item.__parent__ = self

    def get_role(self):
        return self.default_role
