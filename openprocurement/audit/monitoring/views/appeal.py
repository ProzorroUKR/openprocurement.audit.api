# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    APIResource, op_resource
)
from openprocurement.audit.api.utils import context_unpack, json_view
from openprocurement.audit.monitoring.utils import (
    apply_patch, set_author, upload_objects_documents
)
from openprocurement.audit.monitoring.validation import validate_appeal_data


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
