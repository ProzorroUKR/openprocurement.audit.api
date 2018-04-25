# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import (
    op_resource,
    APIResource,
    save_monitor,
    set_documents_of_type,
    apply_patch, set_ownership
)
from openprocurement.api.utils import (
    json_view,
    get_now,
    context_unpack
)
from openprocurement.audit.api.validation import (
    validate_dialogue_data,
    validate_patch_dialogue_data,
    validate_patch_dialogue_allowed
)


@op_resource(name='Monitor Dialogue',
             collection_path='/monitors/{monitor_id}/dialogues',
             path='/monitors/{monitor_id}/dialogues/{dialogue_id}',
             description='Monitor Dialogues')
class DialogueResource(APIResource):

    @json_view(content_type='application/json',
               validators=(validate_dialogue_data,),
               permission='create_dialogue')
    def collection_post(self):
        """
        Post a dialogue
        """
        monitor = self.context
        dialogue = self.request.validated['dialogue']
        dialogue.dateSubmitted = get_now()
        set_ownership(dialogue, self.request, 'author')
        set_documents_of_type(dialogue.documents, 'dialogue')
        monitor.dialogues.append(dialogue)
        if save_monitor(self.request):
            self.LOGGER.info('Created monitor dialogue {}'.format(dialogue.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitor_dialogue_create'},
                                                  {'dialogue_id': dialogue.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                'Monitor Dialogue', monitor_id=monitor.id, dialogue_id=dialogue.id)
            return {'data': dialogue.serialize('view')}

    @json_view(permission='view_monitor')
    def collection_get(self):
        """
        List of dialogues
        """
        return {'data': [i.serialize('view') for i in self.context.dialogues]}

    @json_view(permission='view_monitor')
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
        dialogue = self.request.validated['dialogue']
        dialogue.dateAnswered = get_now()
        apply_patch(self.request, src=self.request.context.serialize())
        self.LOGGER.info('Updated dialogue {}'.format(self.request.context.id),
                         extra=context_unpack(self.request, {'MESSAGE_ID': 'dialogue_patch'}))
        return {'data': self.request.context.serialize('view')}
