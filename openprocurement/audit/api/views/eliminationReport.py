# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
    apply_patch
)
from openprocurement.api.utils import (
    json_view,
    get_now,
    context_unpack
)
from openprocurement.audit.api.validation import (
    validate_patch_elimination_report_data,
    validate_elimination_report_data
)


@op_resource(name='Monitor Elimination',
             path='/monitors/{monitor_id}/eliminationReport',
             description='Elimination of the violation')
class EliminationReportResource(APIResource):

    @json_view(permission='view_monitor')
    def get(self):
        return {'data': self.context.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_elimination_report_data,),
               permission='create_elimination_report')
    def put(self):
        elimination = self.request.validated['eliminationreport']
        elimination.dateModified = elimination.dateCreated
        apply_patch(self.request, data=dict(eliminationReport=elimination), src=self.request.context.serialize())
        self.LOGGER.info('Updated elimination {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'elimination_put'}))
        return {'data': elimination.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_elimination_report_data,),
               permission='edit_elimination_report')
    def patch(self):
        self.request.validated['data']["dateModified"] = get_now()
        apply_patch(self.request, src=self.request.context.serialize())
        self.LOGGER.info('Updated elimination {}'.format(self.request.context.__parent__.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'elimination_patch'}))
        return {'data': self.request.context.serialize('view')}
