from pyramid.security import Allow
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, FloatType, BooleanType, BaseType, MD5Type
from schematics.types.compound import ModelType, DictType
from schematics.types.serializable import serializable
from uuid import uuid4

from openprocurement.audit.api.constants import (
    DECISION_OBJECT_TYPE,
    DRAFT_STATUS,
    OTHER_VIOLATION,
)
from openprocurement.audit.api.constants import SANDBOX_MODE
from openprocurement.audit.api.models import (
    Model, Revision, Document, BaseModel, Party, Identifier, ContactPoint,
    Address,
)
from openprocurement.audit.api.models import schematics_default_role, schematics_embedded_role
from openprocurement.audit.api.types import ListType, IsoDateTimeType
from openprocurement.audit.api.context import get_now
from openprocurement.audit.monitoring.choices import (
    DIALOGUE_TYPE_CHOICES,
    MONITORING_STATUS_CHOICES,
    MONITORING_REASON_CHOICES,
    MONITORING_PROCURING_STAGES,
    RESOLUTION_RESULT_CHOICES,
    RESOLUTION_BY_TYPE_CHOICES,
    PARTY_ROLES_CHOICES,
    LEGISLATION_CHOICES,
    NATIONAL_LEGISLATION_TYPE,
)
from openprocurement.audit.api.choices import VIOLATION_TYPE_CHOICES


class Period(Model):
    startDate = IsoDateTimeType()  # The state date for the period.
    endDate = IsoDateTimeType()  # The end date for the period.

    def validate_startDate(self, data, value):
        if value and data.get('endDate') and data.get('endDate') < value:
            raise ValidationError(u"period should begin before its end")


class LegislationIdentifier(Identifier):
    scheme = StringType()


class Legislation(Model):
    version = StringType()
    identifier = ModelType(LegislationIdentifier)
    type = StringType(choices=LEGISLATION_CHOICES, default=NATIONAL_LEGISLATION_TYPE)
    article = ListType(StringType, min_size=1, required=True)


class Proceeding(Model):
    dateProceedings = IsoDateTimeType(required=True)
    proceedingNumber = StringType(required=True)


class Report(Model):
    description = StringType(required=True)
    documents = ListType(ModelType(Document), default=[])
    dateCreated = IsoDateTimeType(default=get_now)
    datePublished = IsoDateTimeType()


class Post(Model):
    class Options:
        roles = {
            'create': whitelist('title', 'description', 'documents', 'relatedParty', 'relatedPost'),
            'edit': whitelist(),
            'view': schematics_default_role,
            'default': schematics_default_role,
            'embedded': schematics_embedded_role,
        }
    id = MD5Type(required=True, default=lambda: uuid4().hex)

    title = StringType(required=True)
    description = StringType(required=True)
    documents = ListType(ModelType(Document), default=list())
    author = StringType()
    postOf = StringType(choices=DIALOGUE_TYPE_CHOICES, default=DECISION_OBJECT_TYPE)
    datePublished = IsoDateTimeType(default=get_now)
    dateOverdue = IsoDateTimeType()
    relatedPost = StringType()
    relatedParty = StringType()

    def validate_relatedParty(self, data, value):
        parent = data['__parent__']
        if value and isinstance(parent, Model) and value not in [i.id for i in parent.parties]:
            raise ValidationError(u"relatedParty should be one of parties.")

    def validate_relatedPost(self, data, value):
        parent = data['__parent__']
        if value and isinstance(parent, Model):

            # check that another post with 'id'
            # that equals 'relatedPost' of current post exists
            if value not in [i.id for i in parent.posts]:
                raise ValidationError(u"relatedPost should be one of posts of current monitoring.")

            # check that another posts with `relatedPost`
            # that equals `relatedPost` of current post does not exist
            if len([i for i in parent.posts if i.relatedPost == value]) > 1:
                raise ValidationError(u"relatedPost must be unique.")

            related_posts = [i for i in parent.posts if i.id == value]

            # check that there are no multiple related posts,
            # that should never happen coz `id` is unique
            if len(related_posts) > 1:
                raise ValidationError(u"relatedPost can't be a link to more than one post.")

            # check that related post have another author
            if len(related_posts) == 1 and data['author'] == related_posts[0]['author']:
                raise ValidationError(u"relatedPost can't have the same author.")

            # check that related post is not an answer to another post
            if len(related_posts) == 1 and related_posts[0]['relatedPost']:
                raise ValidationError(u"relatedPost can't be have relatedPost defined.")


class Decision(Report):
    date = IsoDateTimeType(required=False)
    relatedParty = StringType()

    def validate_relatedParty(self, data, value):
        parent = data['__parent__']
        if value and isinstance(parent, Model) and value not in [i.id for i in parent.parties]:
            raise ValidationError(u"relatedParty should be one of parties.")


class Conclusion(Report):
    violationOccurred = BooleanType(required=True)
    violationType = ListType(StringType(choices=VIOLATION_TYPE_CHOICES), default=[])
    otherViolationType = StringType()
    auditFinding = StringType()
    stringsAttached = StringType()
    description = StringType(required=False)
    date = IsoDateTimeType(required=False)
    relatedParty = StringType()

    def validate_relatedParty(self, data, value):
        parent = data['__parent__']
        if value and isinstance(parent, Model) and value not in [i.id for i in parent.parties]:
            raise ValidationError(u"relatedParty should be one of parties.")

    def validate_violationType(self, data, value):
        if data["violationOccurred"] and not value:
            raise ValidationError(u"This field is required.")

        if value and OTHER_VIOLATION not in value:  # drop other type description
            data["otherViolationType"] = None

    def validate_otherViolationType(self, data, value):
        if OTHER_VIOLATION in data["violationType"] and not value:
            raise ValidationError(u"This field is required.")


class Cancellation(Report):
    relatedParty = StringType()

    class Options:
        roles = {
            'view': schematics_default_role,
        }

    def validate_relatedParty(self, data, value):
        parent = data['__parent__']
        if value and isinstance(parent, Model) and value not in [i.id for i in parent.parties]:
            raise ValidationError(u"relatedParty should be one of parties.")


class EliminationResolution(Report):
    result = StringType(choices=RESOLUTION_RESULT_CHOICES)
    resultByType = DictType(StringType(choices=RESOLUTION_BY_TYPE_CHOICES))
    description = StringType(required=False)
    relatedParty = StringType()
    
    class Options:
        roles = {
            'view': schematics_default_role,
        }

    def validate_relatedParty(self, data, value):
        parent = data['__parent__']
        if value and isinstance(parent, Model) and value not in [i.id for i in parent.parties]:
            raise ValidationError(u"relatedParty should be one of parties.")

    def validate_resultByType(self, data, value):
        violations = data["__parent__"].conclusion.violationType if data["__parent__"].conclusion else None
        if violations:
            if value is None:
                raise ValidationError(u"This field is required.")
            diff = set(violations) ^ set(value.keys())
            if diff:
                raise ValidationError(u"The field must only contain the following fields: {}".format(
                    ", ".join(violations)))


class EliminationReport(Report):
    class Options:
        roles = {
            'create': whitelist('description', 'documents'),
            'edit': whitelist('description', 'documents'),
            'view': schematics_default_role,
        }


class Appeal(Report):

    proceeding = ModelType(Proceeding)
    legislation = ModelType(Legislation)

    class Options:
        roles = {
            'create': whitelist('description', 'documents'),
            'edit': whitelist('proceeding'),
            'view': schematics_default_role,
        }

    def get_role(self):
        return 'edit'

    @serializable(serialized_name="legislation")
    def fill_legislation(self):
        legislation = {
            'version': '2020-04-19',
            'type': 'NATIONAL_LEGISLATION',
            'article': ['8.10'],
            'identifier': {
                'id': '922-VIII',
                'legalName': 'Закон України "Про публічні закупівлі"',
                'uri': 'https://zakon.rada.gov.ua/laws/show/922-19',
            }
        }
        return legislation


class MonitoringAddress(Address):
    class Options:
        namespace = "Address"

    countryName = StringType(required=True)


class MonitoringContactPoint(ContactPoint):
    class Options:
        namespace = "ContactPoint"

    name = StringType(required=True)

    def validate_email(self, data, value):
        if not value and not data.get('telephone'):
            raise ValidationError(u"telephone or email should be present")


class MonitoringParty(Party):
    class Options:
        namespace = "Party"
        roles = {
            'create': blacklist('id') + schematics_embedded_role,
            'edit': blacklist('id') + schematics_embedded_role,
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
        }

    identifier = ModelType(Identifier, required=True)
    address = ModelType(MonitoringAddress, required=True)
    contactPoint = ModelType(MonitoringContactPoint, required=True)
    roles = ListType(StringType(choices=PARTY_ROLES_CHOICES), default=[])


class Liability(Model):
    class Options:
        roles = {
            'create': whitelist('reportNumber', 'documents', 'legislation'),
            'edit': whitelist('proceeding'),
            'view': schematics_default_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)

    reportNumber = StringType(required=True, min_length=1)
    datePublished = IsoDateTimeType(default=get_now)
    documents = ListType(ModelType(Document), default=[])
    proceeding = ModelType(Proceeding)
    legislation = ModelType(Legislation, required=True)

    def get_role(self):
        return 'edit'

    @serializable(serialized_name="legislation", serialize_when_none=False)
    def fill_legislation(self):
        legislation = {
            'version': '2020-11-21',
            'type': 'NATIONAL_LEGISLATION',
            'article': self.legislation.article,
            'identifier': {
                'id': '8073-X',
                'legalName': 'Кодекс України про адміністративні правопорушення',
                'uri': 'https://zakon.rada.gov.ua/laws/show/80731-10#Text',
            }
        }
        return legislation


class Monitoring(BaseModel):

    class Options:
        _perm_edit_whitelist = whitelist('status', 'reasons', 'procuringStages')
        roles = {
            'plain': blacklist('_attachments', 'revisions') + schematics_embedded_role,
            'revision': whitelist('revisions'),
            'create': whitelist(
                "tender_id", "reasons", "procuringStages", "status",
                "mode", "monitoringDetails", "parties", "decision",
                "riskIndicators", "riskIndicatorsTotalImpact", "riskIndicatorsRegion",
            ),
            'edit_draft': whitelist('decision', 'cancellation') + _perm_edit_whitelist,
            'edit_active': whitelist('conclusion', 'cancellation') + _perm_edit_whitelist,
            'edit_addressed': whitelist('eliminationResolution', 'cancellation') + _perm_edit_whitelist,
            'edit_declined': whitelist('cancellation') + _perm_edit_whitelist,
            'edit_completed': whitelist('documents'),
            'edit_closed': whitelist('documents'),
            'edit_stopped': whitelist('documents', 'status'),
            'edit_cancelled': whitelist('documents'),
            'admins': whitelist('is_masked'),
            'view': blacklist(
                'tender_owner_token', '_attachments', 'revisions', 'public_modified',
                'decision', 'conclusion', 'cancellation'
            ) + schematics_embedded_role,
            'listing': whitelist('dateModified', 'doc_id'),
            'default': schematics_default_role,
        }

    tender_id = MD5Type(required=True)
    monitoring_id = StringType()
    status = StringType(choices=MONITORING_STATUS_CHOICES, default=DRAFT_STATUS)

    reasons = ListType(StringType(choices=MONITORING_REASON_CHOICES), required=True)
    procuringStages = ListType(StringType(choices=MONITORING_PROCURING_STAGES), required=True)
    monitoringPeriod = ModelType(Period)

    documents = ListType(ModelType(Document), default=[])

    riskIndicators = ListType(StringType(), default=[])
    riskIndicatorsTotalImpact = FloatType()
    riskIndicatorsRegion = StringType()

    decision = ModelType(Decision)
    conclusion = ModelType(Conclusion)
    eliminationReport = ModelType(EliminationReport)
    eliminationResolution = ModelType(EliminationResolution)
    eliminationPeriod = ModelType(Period)
    posts = ListType(ModelType(Post), default=[])
    cancellation = ModelType(Cancellation)
    appeal = ModelType(Appeal)
    liabilities = ListType(ModelType(Liability), default=list())

    parties = ListType(ModelType(MonitoringParty), default=[])

    dateModified = IsoDateTimeType()
    endDate = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)
    owner = StringType()
    tender_owner = StringType()
    tender_owner_token = StringType()
    revisions = ListType(ModelType(Revision), default=[])
    _attachments = DictType(DictType(BaseType), default=dict())
    doc_type = StringType(default="Monitoring")

    is_masked = BooleanType()
    restricted = BooleanType()

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

    def get_role(self):
        role = super(Monitoring, self).get_role()
        root = self.__parent__
        request = root.request
        if request.authenticated_role == "admins":
            role = "admins"
        elif role == 'edit':
            status = self.__parent__.request.context.status
            role = f'edit_{status}'
        return role

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_post'),
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_elimination_report'),
            (Allow, '{}_{}'.format(self.tender_owner, self.tender_owner_token), 'create_appeal'),
        ]

    def __repr__(self):
        return '<%s:%r-%r@%r>' % (type(self).__name__, self.tender_id, self.id, self.rev)
