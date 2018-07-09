# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
)
from openprocurement.api.utils import (
    json_view,
)


@op_resource(name='Monitoring Cancellation',
             path='/monitorings/{monitoring_id}/cancellation',
             description='Monitoring Cancellation endpoint')
class CancellationResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}

