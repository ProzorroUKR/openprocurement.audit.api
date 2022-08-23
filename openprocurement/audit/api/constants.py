from logging import getLogger
from datetime import timedelta
from pytz import timezone
from requests import Session
import os.path
import standards


LOGGER = getLogger('openprocurement.audit.api')
VERSION = '2.5'
ROUTE_PREFIX = '/api/{}'.format(VERSION)
SESSION = Session()
SCHEMA_VERSION = 24
SCHEMA_DOC = 'openprocurement_schema'
JOURNAL_PREFIX = os.environ.get('JOURNAL_PREFIX', 'JOURNAL_')
TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')
SANDBOX_MODE = os.environ.get('SANDBOX_MODE', False)
DOCUMENT_BLACKLISTED_FIELDS = ('title', 'format', 'url', 'dateModified', 'hash')
DOCUMENT_WHITELISTED_FIELDS = ('id', 'datePublished', 'author', '__parent__')
WORKING_DAYS = {}
HOLIDAYS = standards.load("calendars/workdays_off.json")
for date_str in HOLIDAYS:
    WORKING_DAYS[date_str] = True
ORA_CODES = [i["code"] for i in standards.load("organizations/identifier_scheme.json")["data"]]

SAS_ROLE = "sas"
PUBLIC_ROLE = "public"

# Time restrictions
MONITORING_TIME = timedelta(days=15)
ELIMINATION_PERIOD_TIME = timedelta(days=10)
ELIMINATION_PERIOD_NO_VIOLATIONS_TIME = timedelta(days=3)
POST_OVERDUE_TIME = timedelta(days=3)
RESOLUTION_WAIT_PERIOD = timedelta(days=5)

# Object type strings
MONITORING_OBJECT_TYPE = 'monitoring'
CANCELLATION_OBJECT_TYPE = 'cancellation'
DECISION_OBJECT_TYPE = 'decision'
CONCLUSION_OBJECT_TYPE = 'conclusion'
APPEAL_OBJECT_TYPE = 'appeal'
LIABILITY_OBJECT_TYPE = 'liability'
ELIMINATION_REPORT_OBJECT_TYPE = 'eliminationReport'
ELIMINATION_RESOLUTION_OBJECT_TYPE = 'eliminationResolution'
POST_OBJECT_TYPE = 'post'

# Monitoring statuses
DRAFT_STATUS = 'draft'
ACTIVE_STATUS = 'active'
ADDRESSED_STATUS = 'addressed'
DECLINED_STATUS = 'declined'
COMPLETED_STATUS = 'completed'
CLOSED_STATUS = 'closed'
STOPPED_STATUS = 'stopped'
CANCELLED_STATUS = 'cancelled'

# Monitoring violation types
CORRUPTION_DESCRIPTION_VIOLATION = 'corruptionDescription'
CORRUPTION_PROCUREMENT_METHOD_TYPE_VIOLATION = 'corruptionProcurementMethodType'
CORRUPTION_PUBLIC_DISCLOSURE_VIOLATION = 'corruptionPublicDisclosure'
CORRUPTION_BIDDING_DOCUMENTS_VIOLATION = 'corruptionBiddingDocuments'
DOCUMENTS_FORM_VIOLATION = 'documentsForm'
CORRUPTION_AWARDED_VIOLATION = 'corruptionAwarded'
CORRUPTION_CANCELLED_VIOLATION = 'corruptionCancelled'
CORRUPTION_CONTRACTING_VIOLATION = 'corruptionContracting'
CORRUPTION_CHANGES_VIOLATION = 'corruptionChanges'
OTHER_VIOLATION = 'other'
CORRUPTION_UNTIMELY = "corruptionUntimely"
CORRUPTION_BID_SECURITY = "corruptionBidSecurity"
CORRUPTION_FAILURE_DOCUMENTS = "corruptionFailureDocuments"
CORRUPTION_CONSIDERATION = "corruptionConsideration"
SERVICES_WITHOUT_PROCUREMENT_PROCEDURE = "servicesWithoutProcurementProcedure"
USE_PROCEDURES_NOT_BY_LAW = "useProceduresNotByLaw"
REJECTION_OF_BIDS_NOT_BY_LAW = "rejectionOfBidsNotByLaw"
INACCURATE_PERSONAL_DATA = "inaccuratePersonalData"
DEADLINE_FOR_THE_PUBLICATION_DOCUMENTATION = "deadlineForThePublicationDocumentation"
NOT_COMPLY_DECISION_ACU = "notComplyDecisionACU"
CONTRACTS_WITHOUT_PROCUREMENT = "contractsWithoutProcurement"

# Legislation violation types

NATIONAL_LEGISLATION_TYPE = "NATIONAL_LEGISLATION"
