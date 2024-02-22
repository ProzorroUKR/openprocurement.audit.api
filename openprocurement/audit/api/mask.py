from jsonpath_ng import parse

from openprocurement.audit.api.auth import ACCR_RESTRICTED


def compile_mask_mapping(mask_mapping):
    """
    Pre-compile the JSONPath expressions in the mask mapping for efficient reuse.
    """
    compiled_mapping = {}
    for path, value in mask_mapping.items():
        compiled_mapping[path] = {
            "value": value,
            "expr": parse(path),
        }
    return compiled_mapping


EXCLUDED_ROLES = (
    "sas",
    "risk_indicators",
    "risk_indicators_api",
    "admins",
)


def mask_object_data(request, data, mask_mapping):
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

    if request.matchdict and request.params and request.matchdict.get("document_id") and request.params.get("download"):
        # Masking is not required when non-authorized user download document by link
        return

    for rule in mask_mapping.values():
        rule["expr"].update(data, rule["value"])
