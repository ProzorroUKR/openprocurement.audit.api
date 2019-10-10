# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    APIResource,
    json_view,
    context_unpack,
)
from openprocurement.audit.monitoring.utils import (
    save_monitoring,
    apply_patch,
    op_resource
)
from openprocurement.audit.monitoring.validation import (
    validate_party_data,
    validate_patch_party_data
)


@op_resource(name='Monitoring Party',
             collection_path='/monitorings/{monitoring_id}/parties',
             path='/monitorings/{monitoring_id}/parties/{party_id}',
             description='Monitoring Parties')
class PartyResource(APIResource):

    @json_view(content_type='application/json',
               validators=(validate_party_data,))
    def collection_post(self):
        """
        Post a party
        """
        monitoring = self.context
        party = self.request.validated['party']
        monitoring.parties.append(party)
        if save_monitoring(self.request):
            self.LOGGER.info('Created monitoring party {}'.format(party.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitoring_party_create'},
                                                  {'party_id': party.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                'Monitoring Party', monitoring_id=monitoring.id, party_id=party.id)
            return {'data': party.serialize('view')}

    @json_view(permission='view_monitoring')
    def collection_get(self):
        """
        List of parties
        """
        return {'data': [i.serialize('view') for i in self.context.parties]}

    @json_view(permission='view_monitoring')
    def get(self):
        """
        Retrieving the party
        """
        return {'data': self.context.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_party_data,),
               permission='edit_party')
    def patch(self):
        """
        Post a party resolution
        """
        apply_patch(self.request)
        self.LOGGER.info('Updated party {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'party_patch'}))
        return {'data': self.request.context.serialize('view')}
