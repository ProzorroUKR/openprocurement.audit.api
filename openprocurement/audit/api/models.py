from uuid import uuid4

from openprocurement.api.constants import SANDBOX_MODE
from openprocurement.api.utils import get_now
from openprocurement.api.models import Model, Revision, Period, Identifier, Address, ContactPoint
from openprocurement.api.models import Document
from openprocurement.api.models import schematics_embedded_role, schematics_default_role, IsoDateTimeType, ListType
from schematics.types import StringType, MD5Type, BaseType, BooleanType
from schematics.types.serializable import serializable
from schematics.types.compound import ModelType, DictType
from schematics.transforms import whitelist, blacklist
from schematics.exceptions import ValidationError
from couchdb_schematics.document import SchematicsDocument
from pyramid.security import Allow


class Report(Model):
    description = StringType(required=True)
    documents = ListType(ModelType(Document), default=list())
    dateCreated = IsoDateTimeType(default=get_now)
    datePublished = IsoDateTimeType()


class Decision(Report):
    date = IsoDateTimeType(required=False)


class Conclusion(Report):
    violationOccurred = BooleanType(required=True)
    violationType = ListType(
        StringType(choices=(
            'corruptionDescription', 'corruptionProcurementMethodType', 'corruptionPublicDisclosure',
            'corruptionBiddingDocuments', 'documentsForm', 'corruptionAwarded', 'corruptionCancelled',
            'corruptionContracting', 'corruptionChanges', 'other',
        )),
        default=[]
    )
    otherViolationType = StringType()
    auditFinding = StringType()
    stringsAttached = StringType()
    description = StringType(required=False)
    date = IsoDateTimeType(required=False)

    def validate_violationType(self, data, value):
        if data["violationOccurred"] and not value:
            raise ValidationError(u"This field is required.")

        if value and "other" not in value:  # drop other type description
            data["otherViolationType"] = None

    def validate_otherViolationType(self, data, value):
        if "other" in data["violationType"] and not value:
            raise ValidationError(u"This field is required.")


class Cancellation(Report):
    pass


class EliminationResolution(Report):
    result = StringType(choices=['completely', 'partly', 'none'])
    resultByType = DictType(StringType(choices=['eliminated', 'not_eliminated', 'no_mechanism']))
    description = StringType(required=False)

    def validate_resultByType(self, data, value):
        violations = data["__parent__"].conclusion.violationType
        if violations:
            if value is None:
                raise ValidationError(u"This field is required.")
            diff = set(violations) ^ set(value.keys())
            if diff:
                raise ValidationError(u"The field must only contain the following fields: {}".format(
                    ", ".join(violations)))


class EliminationReport(Report):
    dateModified = IsoDateTimeType()

    def get_role(self):  # this fixes document validation, because document urls cannot be added when role "edit"
        return 'create'

    class Options:
        roles = {
            'create': whitelist('description', 'documents'),
            'edit': whitelist('description', 'documents'),
            'view': schematics_default_role,
        }

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.__parent__.tender_owner, self.__parent__.tender_owner_token),
             'edit_elimination_report'),
        ]


class Appeal(Report):
    class Options:
        roles = {
            'create': whitelist('description', 'documents'),
            'view': schematics_default_role,
        }


class Dialogue(Model):
    class Options:
        roles = {
            'create': whitelist('title', 'description', 'documents', 'relatedParty'),
            'edit': whitelist('answer'),
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
    dialogueOf = StringType(choices=('decision', 'conclusion'), default='decision')
    relatedParty = StringType()

    def validate_relatedParty(self, data, value):
        if value and isinstance(data['__parent__'], Model) and value not in [i.id for i in data['__parent__'].parties]:
            raise ValidationError(u"relatedParty should be one of parties.")


class Party(Model):
    class Options:
        roles = {
            'create': schematics_embedded_role,
            'edit': schematics_embedded_role,
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }
    id = MD5Type(required=True, default=lambda: uuid4().hex)

    name = StringType(required=True)
    identifier = ModelType(Identifier, required=True)
    additionalIdentifiers = ListType(ModelType(Identifier))
    address = ModelType(Address, required=True)
    contactPoint = ModelType(ContactPoint, required=True)
    roles = ListType(StringType(choices=('create', 'decision', 'conclusion', 'dialogue')), default=list())


class Monitoring(SchematicsDocument, Model):

    class Options:
        _perm_edit_whitelist = whitelist("status", "reasons", "procuringStages", "parties")
        roles = {
            'plain': blacklist('_attachments', 'revisions') + schematics_embedded_role,
            'revision': whitelist('revisions'),
            'create': blacklist(
                'revisions', 'dateModified', 'dateCreated',
                'doc_id', '_attachments', 'monitoring_id',
                'tender_owner_token', 'tender_owner',
                'monitoringPeriod', 'eliminationPeriod'
            ) + schematics_embedded_role,
            'edit_draft': whitelist("decision", "cancellation") + _perm_edit_whitelist,
            'edit_active': whitelist("conclusion", "cancellation") + _perm_edit_whitelist,
            'edit_addressed': whitelist("eliminationResolution", "cancellation") + _perm_edit_whitelist,
            'edit_declined': whitelist("cancellation") + _perm_edit_whitelist,
            'edit_completed': whitelist(),
            'edit_closed': whitelist(),
            'edit_stopped': whitelist(),
            'edit_cancelled': whitelist(),
            'view': blacklist(
                'tender_owner_token', '_attachments', 'revisions',
                'decision', 'conclusion', 'cancellation'
            ) + schematics_embedded_role,
            'listing': whitelist('dateModified', 'doc_id'),
            'default': schematics_default_role,
        }

    tender_id = MD5Type(required=True)
    monitoring_id = StringType()
    status = StringType(choices=[
        'draft', 'active', 'addressed', 'declined',
        'completed', 'closed', 'stopped', 'cancelled'
    ], default='draft')

    reasons = ListType(StringType(choices=['indicator', 'authorities', 'media', 'fiscal', 'public']), required=True)
    procuringStages = ListType(StringType(choices=['planning', 'awarding', 'contracting']), required=True)
    monitoringPeriod = ModelType(Period)

    decision = ModelType(Decision)
    conclusion = ModelType(Conclusion)
    eliminationReport = ModelType(EliminationReport)
    eliminationResolution = ModelType(EliminationResolution)
    eliminationPeriod = ModelType(Period)
    dialogues = ListType(ModelType(Dialogue), default=list())
    cancellation = ModelType(Cancellation)
    appeal = ModelType(Appeal)

    parties = ListType(ModelType(Party), default=list())

    dateModified = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)
    tender_owner = StringType()
    tender_owner_token = StringType()
    revisions = ListType(ModelType(Revision), default=list())
    _attachments = DictType(DictType(BaseType), default=dict())

    mode = StringType(choices=['test'])
    if SANDBOX_MODE:
        monitoringDetails = StringType()

    @serializable(serialized_name='decision', serialize_when_none=False, type=ModelType(Decision))
    def monitoring_decision(self):
        role = self.__parent__.request.authenticated_role
        if self.decision and self.decision.datePublished or role == 'sas':
            return self.decision

    @serializable(serialized_name='conclusion', serialize_when_none=False, type=ModelType(Conclusion))
    def monitoring_conclusion(self):
        role = self.__parent__.request.authenticated_role
        if self.conclusion and self.conclusion.datePublished or role == 'sas':
            return self.conclusion

    @serializable(serialized_name='cancellation', serialize_when_none=False, type=ModelType(Cancellation))
    def monitoring_cancellation(self):
        role = self.__parent__.request.authenticated_role
        if self.cancellation and self.cancellation.datePublished or role == 'sas':
            return self.cancellation

    def validate_eliminationResolution(self, data, value):
        if value is not None and data["eliminationReport"] is None:
            raise ValidationError(u"Elimination report hasn't been provided.")

    def validate_monitoringDetails(self, *args, **kw):
        if self.mode and self.mode == 'test' and self.monitoringDetails and self.monitoringDetails != '':
            raise ValidationError(u"monitoringDetails should be used with mode test.")

    def get_role(self):
        role = super(Monitoring, self).get_role()
        status = self.__parent__.request.context.status
        return 'edit_{}'.format(status) if role == 'edit' else role

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_dialogue'),
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_elimination_report'),
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_appeal'),
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
