# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

# Time restrictions
MONITORING_TIME = timedelta(days=17)
ELIMINATION_PERIOD_TIME = timedelta(days=10)
ELIMINATION_PERIOD_NO_VIOLATIONS_TIME = timedelta(days=3)

# Object type strings
DECISION_OBJECT_TYPE = 'decision'
CONCLUSION_OBJECT_TYPE = 'conclusion'
APPEAL_OBJECT_TYPE = 'appeal'
ELIMINATION_REPORT_OBJECT_TYPE = 'eliminationReport'
POST_OBJECT_TYPE = 'post'

# Custom party roles
CREATE_PARTY_ROLE = 'create'

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
