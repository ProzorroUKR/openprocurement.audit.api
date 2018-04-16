from uuid import uuid4

from openprocurement.api.utils import get_now, get_root
from openprocurement.api.models import Model, Revision, Period
from openprocurement.api.models import Document as BaseDocument
from openprocurement.api.models import schematics_embedded_role, schematics_default_role, IsoDateTimeType, ListType
from schematics.types import StringType, MD5Type, BaseType, BooleanType
from schematics.types.serializable import serializable
from schematics.types.compound import ModelType, DictType
from schematics.transforms import whitelist, blacklist
from schematics.exceptions import ValidationError
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
    'tender_id', 'monitoring_id'
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
    documentOf = StringType(choices=('decision', 'conclusion', 'dialogue'), required=False)
    documentType = StringType()


class Decision(Model):
    description = StringType(required=True)
    date = IsoDateTimeType(required=True)
    documents = ListType(ModelType(Document), default=list())


class Conclusion(Model):
    documents = ListType(ModelType(Document), default=list())

    violationOccurred = BooleanType(required=True)
    violationType = StringType(choices=(
        'corruptionDescription', 'corruptionProcurementMethodType', 'corruptionPublicDisclosure',
        'corruptionBiddingDocuments', 'documentsForm', 'corruptionAwarded', 'corruptionCancelled',
        'corruptionContracting', 'corruptionChanges', 'other',
    ))
    auditFinding = StringType()
    stringsAttached = StringType()
    description = StringType()

    def validate_violationType(self, data, value):
        if data["violationOccurred"] and not value:
            raise ValidationError(u"This field is required.")


class Dialogue(Model):
    class Options:
        roles = {
            'create': whitelist('title', 'description', 'answer', 'documents'),
            'view': blacklist('owner_token', 'owner') + schematics_default_role
        }
    id = MD5Type(required=True, default=lambda: uuid4().hex)

    title = StringType(required=True)
    description = StringType()
    answer = StringType()
    documents = ListType(ModelType(Document), default=list())

    dateSubmitted = IsoDateTimeType()
    dateAnswered = IsoDateTimeType()

    owner_token = StringType()
    owner = StringType()

    def __local_roles__(self):
        return dict(
            [('{}_{}'.format(self.owner, self.owner_token), 'dialogue_owner')]
        )

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_dialogue'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_dialogue_documents')
        ]


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

    tender_id = MD5Type(required=True)
    monitoring_id = StringType()
    status = StringType(choices=['draft', 'active'], default='draft')

    reasons = ListType(StringType(choices=['indicator', 'authorities', 'media', 'fiscal', 'public']), required=True)
    procuringStages = ListType(StringType(choices=['planning', 'awarding', 'contracting']), required=True)
    monitoringPeriod = ModelType(Period)

    decision = ModelType(Decision)
    conclusion = ModelType(Conclusion)
    dialogues = ListType(ModelType(Dialogue), default=list())

    dateModified = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)
    owner_token = StringType()
    owner = StringType()
    revisions = ListType(ModelType(Revision), default=list())
    _attachments = DictType(DictType(BaseType), default=dict())

    def get_role(self):
        root = self.__parent__
        request = root.request
        context = request.context
        if request.authenticated_role in ('Administrator',):
            return request.authenticated_role
        return 'edit_{}'.format(context.status)

    def __local_roles__(self):
        return dict(
            [('{}_{}'.format(self.owner, self.owner_token), 'monitor_owner')]
        )

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_monitor'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_monitor_documents')
        ]

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

    def validate_conclusion(self, data, value):
        if value and data["status"] != "active":
            raise ValidationError(u"Can't manage conclusion in current {} monitor status".format(data["status"]))
