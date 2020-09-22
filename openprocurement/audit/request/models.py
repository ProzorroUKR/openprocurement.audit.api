from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, MD5Type, EmailType
from schematics.types.compound import ModelType

from openprocurement.audit.api.constants import SAS_ROLE, PUBLIC_ROLE
from openprocurement.audit.api.models import (
    Revision,
    Document,
    BaseModel,
    Party,
    Address,
    ContactPoint,
)
from openprocurement.audit.api.models import (
    schematics_default_role,
    schematics_embedded_role,
)
from openprocurement.audit.api.types import IsoDateTimeType, ListType
from openprocurement.audit.api.utils import get_now
from openprocurement.audit.api.choices import VIOLATION_TYPE_CHOICES
from openprocurement.audit.request.choices import REQUEST_PARTY_ROLES_CHOICES


class RequestAddress(Address):
    class Options:
        namespace = "Address"

    streetAddress = StringType(required=True, min_length=1)
    locality = StringType(required=True, min_length=1)
    region = StringType(required=True, min_length=1)
    postalCode = StringType(required=True, min_length=1)
    countryName = StringType(required=True, min_length=1)


class RequestContactPoint(ContactPoint):
    class Options:
        namespace = "ContactPoint"

    email = EmailType(required=True, min_length=1)


class RequestParty(Party):
    class Options:
        namespace = "Party"
        roles = {
            "view": blacklist(
                "address",
                "contactPoint",
                "identifier",
                "additionalIdentifiers",
            ) + schematics_embedded_role,
            "view_%s" % SAS_ROLE: schematics_embedded_role,
        }

    address = ModelType(RequestAddress, required=True)
    contactPoint = ModelType(RequestContactPoint, required=True)
    roles = ListType(
        StringType(choices=REQUEST_PARTY_ROLES_CHOICES),
        default=[PUBLIC_ROLE],
        required=True,
    )


class Request(BaseModel):
    class Options:
        namespace = "Request"
        roles = {
            "plain": blacklist("revisions") + schematics_embedded_role,
            "revision": whitelist("revisions"),
            "create": whitelist(
                "description", "violationType", "documents", "parties", "tenderId", "mode"
            ),
            "edit": whitelist("answer"),
            "view": blacklist("revisions") + schematics_embedded_role,
            "view_%s" % SAS_ROLE: blacklist("revisions") + schematics_embedded_role,
            "view_%s" % PUBLIC_ROLE: blacklist("revisions") + schematics_embedded_role,
            "listing": whitelist("dateModified", "doc_id"),
            "default": schematics_default_role,
        }

    description = StringType(required=True, min_length=1)
    violationType = ListType(
        StringType(choices=VIOLATION_TYPE_CHOICES),
        required=True,
        min_size=1)
    answer = StringType(choices=[
        "monitoringCreated",
        "noViolations",
        "plannedInspection",
        "lawEnforcement",
        "inspectionCreated",
        "plannedMonitoring",
        "noCompetency",
        "tenderCancelled",
        "violationRemoved"
    ])
    dateAnswered = IsoDateTimeType()
    dateModified = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)
    requestId = StringType()
    tenderId = MD5Type(required=True)
    documents = ListType(ModelType(Document, required=True), required=True, min_size=1)
    parties = ListType(ModelType(RequestParty, required=True), required=True, min_size=1)
    revisions = ListType(ModelType(Revision), default=list())

    def __repr__(self):
        return "<%s:%r-%r@%r>" % (
            type(self).__name__,
            self.requestId,
            self.id,
            self.rev,
        )
