from openprocurement.audit.api.views.base import APIResource, json_view
from openprocurement.audit.monitoring.utils import op_resource


@op_resource(name='Monitoring Cancellation',
             path='/monitorings/{monitoring_id}/cancellation',
             description='Monitoring Cancellation endpoint')
class CancellationResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}

