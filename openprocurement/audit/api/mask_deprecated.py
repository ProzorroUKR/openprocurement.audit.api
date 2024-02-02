EXCLUDED_FIELDS = {
    "mode",
    "owner",
    "author",
    "scheme",
    "_id",
    "id",
    "monitoring_id",
    "reasons",
    "procuringStages",
    "violationType",
    "result",
    "resultByType",
    "relatedParty",
    "relatedPost",
    "roles",
    "type",
    "postOf",
    "tender_id",
    "hash",
    "owner_token",
    "status",
    "next_check",
}

EXCLUDED_ROLES = (
    "Administrator",
)


def mask_simple_data(v):
    if isinstance(v, str):
        v = "0" * len(v)
    elif isinstance(v, bool):
        pass
    elif isinstance(v, int) or isinstance(v, float):
        v = 0
    return v


def ignore_mask(key):
    ignore_keys = EXCLUDED_FIELDS
    if key in ignore_keys:
        return True
    elif key.startswith("date") or key.endswith("Date"):
        return True


def mask_process_compound(data):
    if isinstance(data, list):
        data = [mask_process_compound(e) for e in data]
    elif isinstance(data, dict):
        for i, j in data.items():
            if not ignore_mask(i):
                j = mask_process_compound(j)
                if i == "identifier":  # identifier.id
                    j["id"] = mask_simple_data(j["id"])
            data[i] = j
    else:
        data = mask_simple_data(data)
    return data


def mask_object_data_deprecated(request, data):
    is_masked = data.get("is_masked", False)
    if not is_masked:
        return

    if request.authenticated_role in EXCLUDED_ROLES:
        # Masking is not required for these roles
        return

    revisions = data.pop("revisions", [])
    mask_process_compound(data)
    data["revisions"] = revisions
