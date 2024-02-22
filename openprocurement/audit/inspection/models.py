from schematics.transforms import whitelist, blacklist
from schematics.types import BooleanType, StringType, MD5Type, BaseType
from schematics.types.compound import ModelType, DictType
from openprocurement.audit.api.models import Revision, Document, BaseModel
from openprocurement.audit.api.models import schematics_default_role, schematics_embedded_role
from openprocurement.audit.api.types import IsoDateTimeType, ListType
from openprocurement.audit.api.context import get_now


class Inspection(BaseModel):
    class Options:
        roles = {
            'plain': blacklist('_attachments', 'revisions') + schematics_embedded_role,
            'revision': whitelist('revisions'),
            'create': blacklist(
                'revisions', 'dateModified', 'dateCreated',
                'doc_id', '_attachments', 'inspection_id'
            ) + schematics_embedded_role,
            'edit': whitelist("description", "monitoring_ids"),
            'view': blacklist(
                '_attachments',
                'revisions',
                'public_modified',
            ) + schematics_embedded_role,
            'listing': whitelist('dateModified', 'doc_id'),
            'default': schematics_default_role,
        }

    monitoring_ids = ListType(MD5Type, required=True, min_size=1)
    description = StringType(required=True)

    documents = ListType(ModelType(Document), default=list())
    inspection_id = StringType()
    dateModified = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)

    revisions = ListType(ModelType(Revision), default=list())
    _attachments = DictType(DictType(BaseType), default=dict())
    doc_type = StringType(default="Inspection")

    restricted = BooleanType()

    def __repr__(self):
        return '<%s:%r-%r@%r>' % (type(self).__name__, self.inspection_id, self.id, self.rev)
