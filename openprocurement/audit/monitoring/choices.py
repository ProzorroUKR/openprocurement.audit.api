from openprocurement.audit.api.constants import (
    DECISION_OBJECT_TYPE, CONCLUSION_OBJECT_TYPE, DRAFT_STATUS, ACTIVE_STATUS, ADDRESSED_STATUS,
    DECLINED_STATUS, COMPLETED_STATUS, CLOSED_STATUS, STOPPED_STATUS, CANCELLED_STATUS
)
DIALOGUE_TYPE_CHOICES = (
    DECISION_OBJECT_TYPE,
    CONCLUSION_OBJECT_TYPE,
)

PARTY_ROLES_CHOICES = (
    'sas',
    'risk_indicator'
)

MONITORING_STATUS_CHOICES = (
    DRAFT_STATUS,
    ACTIVE_STATUS,
    ADDRESSED_STATUS,
    DECLINED_STATUS,
    COMPLETED_STATUS,
    CLOSED_STATUS,
    STOPPED_STATUS,
    CANCELLED_STATUS,
)

MONITORING_REASON_CHOICES = [
    'indicator',
    'authorities',
    'media',
    'fiscal',
    'public'
]

MONITORING_PROCURING_STAGES = [
    'planning',
    'awarding',
    'contracting'
]

RESOLUTION_RESULT_CHOICES = [
    'completely',
    'partly',
    'none'
]

RESOLUTION_BY_TYPE_CHOICES = [
    'eliminated',
    'not_eliminated',
    'no_mechanism'
]

PROCEEDING_TYPE_CHOICES = (
    'sas',
    'court',
)
