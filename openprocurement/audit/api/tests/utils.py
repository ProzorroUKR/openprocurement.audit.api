def get_errors_field_names(response, description=None):
    return {
        (error['location'], error['name']) for error in response.json.get('errors', [])
        if not description or description in error['description']
    }
