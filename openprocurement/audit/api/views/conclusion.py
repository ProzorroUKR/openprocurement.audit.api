# -*- coding: utf-8 -*-
from openprocurement.api.utils import forbidden
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
)
from openprocurement.audit.api.constants import ACTIVE_STATUS
from openprocurement.api.utils import (
    json_view,
)


@op_resource(name='Monitoring Conclusion',
             path='/monitorings/{monitoring_id}/conclusion',
             description='Monitoring Conclusion endpoint')
class ConclusionResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        if self.request.validated['monitoring'].status == ACTIVE_STATUS \
            and not self.request.has_permission('view_draft_monitoring'):
                return forbidden(self.request)
        return {'data': self.context.serialize('default')}

