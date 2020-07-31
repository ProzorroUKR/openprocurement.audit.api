from hashlib import algorithms_guaranteed, new as hash_new

from datetime import datetime
from iso8601 import parse_date, ParseError
from schematics.exceptions import ValidationError, ConversionError
from schematics.types import BaseType, StringType
from schematics.types.compound import ListType as BaseListType

from openprocurement.audit.api.constants import TZ


class HashType(StringType):

    MESSAGES = {
        'hash_invalid': "Hash type is not supported.",
        'hash_length': "Hash value is wrong length.",
        'hash_hex': "Hash value is not hexadecimal.",
    }

    def to_native(self, value, context=None):
        value = super(HashType, self).to_native(value, context)

        if ':' not in value:
            raise ValidationError(self.messages['hash_invalid'])

        hash_type, hash_value = value.split(':', 1)

        if hash_type not in algorithms_guaranteed:
            raise ValidationError(self.messages['hash_invalid'])

        if len(hash_value) != hash_new(hash_type).digest_size * 2:
            raise ValidationError(self.messages['hash_length'])
        try:
            int(hash_value, 16)
        except ValueError:
            raise ConversionError(self.messages['hash_hex'])
        return value


class ListType(BaseListType):

    def export_loop(self, list_instance, field_converter,
                    role=None, print_none=False):
        """Loops over each item in the model and applies either the field
        transform or the multitype transform.  Essentially functions the same
        as `transforms.export_loop`.
        """
        data = []
        for value in list_instance:
            if hasattr(self.field, 'export_loop'):
                shaped = self.field.export_loop(value, field_converter,
                                                role=role,
                                                print_none=print_none)
                feels_empty = shaped and len(shaped) == 0
            else:
                shaped = field_converter(self.field, value)
                feels_empty = shaped is None

            # Print if we want empty or found a value
            if feels_empty and self.field.allow_none():
                data.append(shaped)
            elif shaped is not None:
                data.append(shaped)
            elif print_none:
                data.append(shaped)

        # Return data if the list contains anything
        if len(data) > 0:
            return data
        elif len(data) == 0 and self.allow_none():
            return data
        elif print_none:
            return data


class IsoDateTimeType(BaseType):
    MESSAGES = {
        'parse': u'Could not parse {0}. Should be ISO8601.',
    }

    def to_native(self, value, context=None):
        if isinstance(value, datetime):
            return value
        try:
            date = parse_date(value, None)
            if not date.tzinfo:
                date = TZ.localize(date)
            return date
        except ParseError:
            raise ConversionError(self.messages['parse'].format(value))
        except OverflowError as e:
            raise ConversionError(e.message)

    def to_primitive(self, value, context=None):
        return value.isoformat()
