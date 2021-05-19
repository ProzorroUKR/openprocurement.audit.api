# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    APIResource
)
from openprocurement.audit.api.utils import context_unpack, json_view
from openprocurement.audit.monitoring.utils import (
    apply_patch, set_author, op_resource, save_monitoring,
)
from openprocurement.audit.monitoring.validation import (
    validate_liability_data,
    validate_patch_liability_data,
)


@op_resource(
    name="Monitoring Liability",
    collection_path="/monitorings/{monitoring_id}/liabilities",
    path="/monitorings/{monitoring_id}/liabilities/{liability_id}",
    description="Liability to the conclusion"
)
class LiabilityResource(APIResource):

    @json_view(
        content_type='application/json',
        validators=(
            validate_liability_data,
        ),
        permission='edit_monitoring'
    )
    def collection_post(self):

        monitoring = self.context
        liability = self.request.validated['liability']
        set_author(liability.documents, self.request, 'author')
        # upload_objects_documents(self.request, liability)
        monitoring.liabilities.append(liability)
        if save_monitoring(self.request):
            self.LOGGER.info('Created monitoring liability {}'.format(liability.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'liability_create'},
                                                  {'liability_id': liability.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                'Monitoring Liability', monitoring_id=monitoring.id, liability_id=liability.id)
            return {'data': liability.serialize('view')}

    @json_view(
        content_type='application/json',
        validators=(
            validate_patch_liability_data,
        ),
        permission='edit_monitoring',
    )
    def patch(self):
        apply_patch(self.request)
        self.LOGGER.info('Updated liability {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'liability_patch'}))
        return {'data': self.request.context.serialize('view')}

    @json_view(permission='view_monitoring')
    def get(self):
        return {'data': self.context.serialize('view')}

    @json_view(permission='view_monitoring')
    def collection_get(self):
        """
        List of parties
        """
        return {'data': [i.serialize('view') for i in self.context.liabilities]}
