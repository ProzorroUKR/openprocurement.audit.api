# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
    apply_patch,
    set_ownership,
)
from openprocurement.api.utils import (
    json_view,
    get_now,
    context_unpack
)
from openprocurement.audit.api.validation import validate_appeal_data


@op_resource(name='Monitoring Appeal',
             path='/monitorings/{monitoring_id}/appeal',
             description='appeal to the conclusion')
class AppealResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_appeal_data,),
               permission='create_appeal')
    def put(self):
        appeal = self.request.validated['appeal']
        set_ownership(appeal.documents, self.request, 'author')
        appeal.datePublished = appeal.dateCreated

        apply_patch(self.request, data=dict(appeal=appeal))
        self.LOGGER.info('Updated appeal {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'appeal_put'}))
        return {'data': appeal.serialize('view')}
