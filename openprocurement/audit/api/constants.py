# -*- coding: utf-8 -*-
import os
from logging import getLogger

from datetime import timedelta
from pytz import timezone
from requests import Session


def read_json(name):
    import os.path
    from json import loads
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(curr_dir, 'data', name)
    with open(file_path) as lang_file:
        data = lang_file.read()
    return loads(data)

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
WORKING_DAYS = read_json('working_days.json')
ORA_CODES = [i['code'] for i in read_json('OrganisationRegistrationAgency.json')['data']]

# Time restrictions
MONITORING_TIME = timedelta(days=15)
ELIMINATION_PERIOD_TIME = timedelta(days=10)
ELIMINATION_PERIOD_NO_VIOLATIONS_TIME = timedelta(days=3)
POST_OVERDUE_TIME = timedelta(days=3)

# Object type strings
MONITORING_OBJECT_TYPE = 'monitoring'
CANCELLATION_OBJECT_TYPE = 'cancellation'
DECISION_OBJECT_TYPE = 'decision'
CONCLUSION_OBJECT_TYPE = 'conclusion'
APPEAL_OBJECT_TYPE = 'appeal'
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
