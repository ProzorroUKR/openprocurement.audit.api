# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import APIResource, json_view
from openprocurement.audit.monitoring.utils import op_resource


@op_resource(name='Monitoring Elimination Resolution',
             path='/monitorings/{monitoring_id}/eliminationResolution',
             description='Monitoring Elimination Resolution endpoint')
class EliminationResolutionResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}
