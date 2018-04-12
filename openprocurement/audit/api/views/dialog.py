# -*- coding: utf-8 -*-
from openprocurement.audit.api.utils import op_resource, APIResource, save_monitor, set_documents_of_type
from openprocurement.api.utils import (
    json_view,
    set_ownership,
    get_now,
    context_unpack)
from openprocurement.audit.api.validation import validate_dialogue_data


@op_resource(name='Monitor Dialogue',
             collection_path='/monitors/{monitor_id}/dialogues',
             path='/monitors/{monitor_id}/dialogues/{dialogue_id}',
             description='Monitor Dialogues')
class DialogueResource(APIResource):

    @json_view(content_type="application/json", validators=(validate_dialogue_data,), permission='create_dialogue')
    def collection_post(self):
        """
        Post a dialogue
        """
        monitor = self.context
        dialogue = self.request.validated['dialogue']
        dialogue.dateSubmitted = get_now()
        set_ownership(dialogue, self.request)
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
            return {
                'data': dialogue.serialize('view'),
                'access': {
                    'token': dialogue.owner_token
                }
            }

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

    @json_view(content_type="application/json", validators=(), permission='edit_dialogue')
    def patch(self):
        """
        Post a dialogue resolution
        """
        raise NotImplementedError
