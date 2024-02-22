from openprocurement.audit.api.mask import compile_mask_mapping

MASK_STRING = "Приховано"
MASK_STRING_EN = "Hidden"


INSPECTION_MASK_MAPPING = compile_mask_mapping({
    "$.description": MASK_STRING,

    # documents
    "$.documents[*].title": MASK_STRING,
    "$.documents[*].title_ru": MASK_STRING,
    "$.documents[*].title_en": MASK_STRING_EN,
    "$.documents[*].url": MASK_STRING,
})
