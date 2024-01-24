from jsonpath_ng import parse

from openprocurement.audit.api.auth import ACCR_RESTRICTED

MASK_STRING = "Приховано"
MASK_STRING_EN = "Hidden"


MONITORING_MASK_MAPPING = {
    # decision
    "$.decision.description": MASK_STRING,
    "$.decision.documents[*].title": MASK_STRING,
    "$.decision.documents[*].title_ru": MASK_STRING,
    "$.decision.documents[*].title_en": MASK_STRING_EN,
    "$.decision.documents[*].url": MASK_STRING,

    # conclusion
    "$.conclusion.auditFinding": MASK_STRING,
    "$.conclusion.stringsAttached": MASK_STRING,
    "$.conclusion.description": MASK_STRING,
    "$.conclusion.documents[*].title": MASK_STRING,
    "$.conclusion.documents[*].title_ru": MASK_STRING,
    "$.conclusion.documents[*].title_en": MASK_STRING_EN,
    "$.conclusion.documents[*].url": MASK_STRING,

    # cancellation
    "$.cancellation.description": MASK_STRING,
    "$.cancellation.documents[*].title": MASK_STRING,
    "$.cancellation.documents[*].title_ru": MASK_STRING,
    "$.cancellation.documents[*].title_en": MASK_STRING_EN,
    "$.cancellation.documents[*].url": MASK_STRING,

    # posts
    "$.posts[*].title": MASK_STRING,
    "$.posts[*].description": MASK_STRING,
    "$.posts[*].documents[*].title": MASK_STRING,
    "$.posts[*].documents[*].title_ru": MASK_STRING,
    "$.posts[*].documents[*].title_en": MASK_STRING_EN,
    "$.posts[*].documents[*].url": MASK_STRING,

    # eliminationReport
    "$.eliminationReport.description": MASK_STRING,
    "$.eliminationReport.documents[*].title": MASK_STRING,
    "$.eliminationReport.documents[*].title_ru": MASK_STRING,
    "$.eliminationReport.documents[*].title_en": MASK_STRING_EN,
    "$.eliminationReport.documents[*].url": MASK_STRING,

    # eliminationResolution
    "$.eliminationResolution.description": MASK_STRING,
    "$.eliminationResolution.documents[*].title": MASK_STRING,
    "$.eliminationResolution.documents[*].title_ru": MASK_STRING,
    "$.eliminationResolution.documents[*].title_en": MASK_STRING_EN,
    "$.eliminationResolution.documents[*].url": MASK_STRING,

    # appeal
    "$.appeal.description": MASK_STRING,
    "$.appeal.documents[*].title": MASK_STRING,
    "$.appeal.documents[*].title_ru": MASK_STRING,
    "$.appeal.documents[*].title_en": MASK_STRING_EN,
    "$.appeal.documents[*].url": MASK_STRING,

    # documents
    "$.documents[*].title": MASK_STRING,
    "$.documents[*].title_ru": MASK_STRING,
    "$.documents[*].title_en": MASK_STRING_EN,
    "$.documents[*].url": MASK_STRING,
}

EXCLUDED_ROLES = (
    "sas",
    "risk_indicators",
    "risk_indicators_api",
    "admins",
)


def mask_object_data(request, data):
    if not data.get("restricted", False):
        # Masking only enabled if restricted is True
        return

    if request.authenticated_role in EXCLUDED_ROLES:
        # Masking is not required for these roles
        return

    if request.authenticated_role == "brokers" and request.check_accreditation(ACCR_RESTRICTED):
        # Masking is not required for brokers with accreditation
        # that allows access to restricted data
        return

    for json_path, replacement_value in MONITORING_MASK_MAPPING.items():
        jsonpath_expr = parse(json_path)
        jsonpath_expr.update(data, replacement_value)
