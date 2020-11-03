# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    APIResource
)
from openprocurement.audit.api.utils import context_unpack, json_view
from openprocurement.audit.monitoring.utils import (
    apply_patch, set_author, upload_objects_documents, op_resource
)
from openprocurement.audit.monitoring.validation import validate_appeal_data, validate_patch_appeal_data


@op_resource(name='Monitoring Appeal',
             path='/monitorings/{monitoring_id}/appeal',
             description='Appeal to the conclusion')
class AppealResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_appeal_data,),
               permission='create_appeal')
    def put(self):
        appeal = self.request.validated['appeal']
        set_author(appeal.documents, self.request, 'author')
        upload_objects_documents(self.request, appeal)
        appeal.datePublished = appeal.dateCreated

        apply_patch(self.request, data=dict(appeal=appeal))
        self.LOGGER.info('Updated appeal {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'appeal_put'}))
        return {'data': appeal.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_appeal_data,),
               permission='create_appeal')
    def patch(self):
        appeal = self.request.context
        monitoring = self.request.validated['monitoring']
        apply_patch(self.request, save=False, src=appeal.serialize())
        self.LOGGER.info('Updated appeal {}'.format(monitoring.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'appeal_patch'}))
        return {'data': appeal.serialize('view')}
