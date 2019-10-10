# -*- coding: utf-8 -*-
from openprocurement.audit.api.constants import DRAFT_STATUS
from openprocurement.audit.api.utils import APIResource, forbidden, json_view
from openprocurement.audit.monitoring.utils import op_resource


@op_resource(name='Monitoring Decision',
             path='/monitorings/{monitoring_id}/decision',
             description='Monitoring Decision endpoint')
class DecisionResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        if self.request.validated['monitoring'].status == DRAFT_STATUS \
            and not self.request.has_permission('view_draft_monitoring'):
                return forbidden(self.request)
        return {'data': self.context.serialize('default')}

