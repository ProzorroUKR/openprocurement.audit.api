# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
    save_monitoring,
    apply_patch,
    set_ownership,
    set_author)
from openprocurement.api.utils import (
    json_view,
    get_now,
    context_unpack
)
from openprocurement.audit.api.validation import (
    validate_dialogue_data,
    validate_patch_dialogue_data,
    validate_patch_dialogue_allowed,
    validate_post_dialogue_allowed
)


@op_resource(name='Monitoring Dialogue',
             collection_path='/monitorings/{monitoring_id}/dialogues',
             path='/monitorings/{monitoring_id}/dialogues/{dialogue_id}',
             description='Monitoring Dialogues')
class DialogueResource(APIResource):

    @json_view(content_type='application/json',
               validators=(validate_dialogue_data, validate_post_dialogue_allowed),
               permission='create_dialogue')
    def collection_post(self):
        """
        Post a dialogue
        """
        monitoring = self.context
        dialogue = self.request.validated['dialogue']
        dialogue.dateSubmitted = get_now()
        set_author(dialogue, self.request, 'author')
        set_author(dialogue.documents, self.request, 'author')
        if monitoring.status in ('addressed', 'declined'):
            dialogue.dialogueOf = 'conclusion'
        monitoring.dialogues.append(dialogue)
        if save_monitoring(self.request):
            self.LOGGER.info('Created monitoring dialogue {}'.format(dialogue.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitoring_dialogue_create'},
                                                  {'dialogue_id': dialogue.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                'Monitoring Dialogue', monitoring_id=monitoring.id, dialogue_id=dialogue.id)
            return {'data': dialogue.serialize('view')}

    @json_view(permission='view_monitoring')
    def collection_get(self):
        """
        List of dialogues
        """
        return {'data': [i.serialize('view') for i in self.context.dialogues]}

    @json_view(permission='view_monitoring')
    def get(self):
        """
        Retrieving the dialogue
        """
        return {'data': self.context.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_dialogue_data, validate_patch_dialogue_allowed),
               permission='edit_dialogue')
    def patch(self):
        """
        Post a dialogue resolution
        """
        self.request.context.dateAnswered = get_now()
        apply_patch(self.request)
        self.LOGGER.info('Updated dialogue {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'dialogue_patch'}))
        return {'data': self.request.context.serialize('view')}
