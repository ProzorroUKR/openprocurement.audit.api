def get_errors_field_names(response, text=None):
    for error in response.json.get('errors', []):
        if text:
            descriptions = error['description'] if isinstance(error['description'], list) else [error['description']]

            if text in descriptions:
                yield (error['location'], error['name'])
            else:
                for description in descriptions:
                    if isinstance(description, dict):
                        for name, value in description.items():
                            if text in value:
                                yield (error['location'], error['name'], name)

        else:
            yield (error['location'], error['name'])
