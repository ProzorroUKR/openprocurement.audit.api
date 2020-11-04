# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    APIResource
)
from openprocurement.audit.api.utils import context_unpack, json_view
from openprocurement.audit.monitoring.utils import (
    apply_patch, set_author, upload_objects_documents, op_resource
)
from openprocurement.audit.monitoring.validation import validate_liability_data, validate_patch_liability_data


@op_resource(name='Monitoring Liability',
             path='/monitorings/{monitoring_id}/liability',
             description='Liability to the conclusion')
class LiabilityResource(APIResource):

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_liability_data,),
               permission='edit_monitoring')
    def put(self):
        liability = self.request.validated['liability']
        set_author(liability.documents, self.request, 'author')
        upload_objects_documents(self.request, liability)

        apply_patch(self.request, data=dict(liability=liability))
        self.LOGGER.info('Updated liability {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'liability_put'}))
        return {'data': liability.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_liability_data,),
               permission='edit_monitoring')
    def patch(self):
        liability = self.request.context
        monitoring = self.request.validated['monitoring']
        apply_patch(self.request, src=liability.serialize())
        self.LOGGER.info('Updated liability {}'.format(monitoring.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'liability_patch'}))
        return {'data': liability.serialize('view')}
