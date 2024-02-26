from openprocurement.audit.api.mask import compile_mask_mapping

MASK_STRING = "Приховано"
MASK_STRING_EN = "Hidden"


MONITORING_MASK_MAPPING = compile_mask_mapping({
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

    # liabilities
    "$.liabilities[*].documents[*].title": MASK_STRING,
    "$.liabilities[*].documents[*].title_ru": MASK_STRING,
    "$.liabilities[*].documents[*].title_en": MASK_STRING_EN,
    "$.liabilities[*].documents[*].url": MASK_STRING,

    # documents
    "$.documents[*].title": MASK_STRING,
    "$.documents[*].title_ru": MASK_STRING,
    "$.documents[*].title_en": MASK_STRING_EN,
    "$.documents[*].url": MASK_STRING,
})
