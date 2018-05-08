# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
    save_monitor,
    apply_patch,
)
from openprocurement.api.utils import (
    json_view,
    context_unpack
)
from openprocurement.audit.api.validation import (
    validate_party_data,
    validate_patch_party_data
)


@op_resource(name='Monitor Party',
             collection_path='/monitors/{monitor_id}/parties',
             path='/monitors/{monitor_id}/parties/{party_id}',
             description='Monitor Parties')
class PartyResource(APIResource):

    @json_view(content_type='application/json',
               validators=(validate_party_data,))
    def collection_post(self):
        """
        Post a party
        """
        monitor = self.context
        party = self.request.validated['party']
        monitor.parties.append(party)
        if save_monitor(self.request):
            self.LOGGER.info('Created monitor party {}'.format(party.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitor_party_create'},
                                                  {'party_id': party.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                'Monitor Party', monitor_id=monitor.id, party_id=party.id)
            return {'data': party.serialize('view')}

    @json_view(permission='view_monitor')
    def collection_get(self):
        """
        List of parties
        """
        return {'data': [i.serialize('view') for i in self.context.parties]}

    @json_view(permission='view_monitor')
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
