from openprocurement.api.utils import get_now
from openprocurement.api.models import Model, Revision, Period
from openprocurement.api.models import Document as BaseDocument
from openprocurement.api.models import schematics_embedded_role, schematics_default_role, IsoDateTimeType, ListType
from schematics.types import StringType, MD5Type
from schematics.types.serializable import serializable
from schematics.types.compound import ModelType
from schematics.transforms import whitelist, blacklist
from couchdb_schematics.document import SchematicsDocument
from pyramid.security import Allow


# roles
plain_role = blacklist(
    '_attachments', 'revisions',
) + schematics_embedded_role

create_role = blacklist(
    'owner_token', 'owner', 'revisions', 'dateModified',
    'dateCreated', 'monitoringPeriod', 'doc_id', '_attachments',
    'monitoring_id'
) + schematics_embedded_role

edit_draft_role = blacklist(
    'owner_token', 'owner', 'revisions', 'dateModified',
    'dateCreated', 'monitoringPeriod', 'doc_id', '_attachments',
    'tender_id', 'monitoring_id'
) + schematics_embedded_role

edit_active_role = blacklist(
    'owner_token', 'owner', 'revisions', 'dateModified',
    'dateCreated', 'monitoringPeriod', 'doc_id', '_attachments',
    'tender_id', 'monitoring_id', 'decision'
) + schematics_embedded_role

view_role = blacklist(
    'owner_token', '_attachments', 'revisions'
) + schematics_embedded_role

listing_role = whitelist(
    'dateModified', 'doc_id'
)

revision_role = whitelist(
    'revisions'
)


class Document(BaseDocument):
    documentOf = StringType(choices=('decision', 'conclusion'), required=False)


class Decision(Model):
    description = StringType(required=True)
    date = IsoDateTimeType(required=True)
    documents = ListType(ModelType(Document), default=list(), required=True)

class Conclusion(Model):
    description = StringType(required=True)
    date = IsoDateTimeType(required=True)
    documents = ListType(ModelType(Document), default=list())


class Monitor(SchematicsDocument, Model):

    class Options:
        roles = {
            'plain': plain_role,
            'revision': revision_role,
            'create': create_role,
            'edit_draft': edit_draft_role,
            'edit_active': edit_active_role,
            'view': view_role,
            'listing': listing_role,
            'default': schematics_default_role,
        }

    # fields
    tender_id = MD5Type(required=True)
    monitoring_id = StringType()
    status = StringType(choices=['draft', 'active'], default='draft')

    reasons = ListType(StringType(choices=['indicator', 'authorities', 'media', 'fiscal', 'public']), required=True)
    procuringStages = ListType(StringType(choices=['planning', 'awarding', 'contracting']), required=True)
    monitoringPeriod = ModelType(Period)

    decision = ModelType(Decision)
    conclusion = ModelType(Conclusion)

    dateModified = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)
    owner_token = StringType()
    owner = StringType()
    revisions = ListType(ModelType(Revision), default=list())

    __name__ = ''

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role in ('Administrator',):
            return request.authenticated_role
        else:
            return 'edit_{}'.format(request.context.status)

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_monitor'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_monitor_documents'),
        ]
        return acl

    def __repr__(self):
        return '<%s:%r-%r@%r>' % (type(self).__name__, self.tender_id, self.id, self.rev)

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
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
