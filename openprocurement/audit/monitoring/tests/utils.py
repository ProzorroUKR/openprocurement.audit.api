def get_errors_field_names(response, text=None):
    for error in response.json.get('errors', []):
        location = (error['location'], error['name'])
        if text:
            if isinstance(error['description'], list):
                descriptions = error['description']
            else:
                descriptions = [error['description']]
            if text in descriptions:
                yield location
            else:
                for item in descriptions:
                    yield from get_errors_sub_field_names(item, text, location)
        else:
            yield location


def get_errors_sub_field_names(item, text, location):
    if isinstance(item, dict):
        for name, value in item.items():
            yield from get_errors_sub_field_names(value, text, location + (name,))
    else:
        if text in item:
            yield location
