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
            'create': whitelist('title', 'description', 'documents'),
            'edit': whitelist('answer', 'documents'),
            'view': schematics_default_role,
            'default': schematics_default_role,
            'embedded': schematics_embedded_role,
        }
    id = MD5Type(required=True, default=lambda: uuid4().hex)

    title = StringType(required=True)
    description = StringType(required=True)
    answer = StringType()
    documents = ListType(ModelType(Document), default=list())
    dateSubmitted = IsoDateTimeType(default=get_now())
    dateAnswered = IsoDateTimeType()
    author = StringType()


class Monitor(SchematicsDocument, Model):

    class Options:
        roles = {
            'plain': blacklist('_attachments', 'revisions') + schematics_embedded_role,
            'revision': whitelist('revisions'),
            'create': blacklist(
                'revisions', 'dateModified', 'dateCreated', 'monitoringPeriod',
                'doc_id', '_attachments', 'monitoring_id',
                'tender_owner_token', 'tender_owner'
            ) + schematics_embedded_role,
            'edit_draft': blacklist(
                'revisions', 'dateModified', 'dateCreated', 'monitoringPeriod',
                'doc_id', '_attachments', 'tender_id', 'monitoring_id',
                'tender_owner_token', 'tender_owner'
            ) + schematics_embedded_role,
            'edit_active': blacklist(
                'revisions', 'dateModified', 'dateCreated', 'monitoringPeriod',
                'doc_id', '_attachments', 'tender_id', 'monitoring_id', 'decision',
                'tender_owner_token', 'tender_owner'
            ) + schematics_embedded_role,
            'view': blacklist(
                'tender_owner_token', '_attachments', 'revisions'
            ) + schematics_embedded_role,
            'listing': whitelist('dateModified', 'doc_id'),
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
    tender_owner = StringType()
    tender_owner_token = StringType()
    revisions = ListType(ModelType(Revision), default=list())
    _attachments = DictType(DictType(BaseType), default=dict())

    def get_role(self):
        role = super(Monitor, self).get_role()
        status = self.__parent__.request.context.status
        return 'edit_{}'.format(status) if role == 'edit' else role

    def __local_roles__(self):
        return dict([
            ('{}_{}'.format(self.tender_owner, self.tender_owner_token), 'tender_owner'),
        ])

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_dialogue'),
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'edit_dialogue'),
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'upload_dialogue_documents'),
        ]

    def __repr__(self):
        return '<%s:%r-%r@%r>' % (type(self).__name__, self.tender_id, self.id, self.rev)

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
