# -*- coding: utf-8 -*-
from cornice.service import Service
from pyramid.response import Response

health = Service(name='health', path='/health', renderer='json')
HEALTH_THRESHOLD_FUNCTIONS = {
    'any': any,
    'all': all
}


@health.get()
def get_health(request):
    return Response(json_body={}, status=200)
