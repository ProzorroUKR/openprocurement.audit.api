# -*- coding: utf-8 -*-
from openprocurement.audit.api.constants import (
    CONCLUSION_OBJECT_TYPE,
    ADDRESSED_STATUS,
    DECLINED_STATUS,
    POST_OVERDUE_TIME,
)
from openprocurement.audit.api.utils import (
    get_now, context_unpack, APIResource, json_view
)
from openprocurement.audit.monitoring.utils import (
    save_monitoring, set_author,
    get_monitoring_role, get_monitoring_accelerator,
    calculate_normalized_business_date, upload_objects_documents,
    op_resource,
)
from openprocurement.audit.monitoring.validation import (
    validate_post_data,
)


@op_resource(name='Monitoring Post',
             collection_path='/monitorings/{monitoring_id}/posts',
             path='/monitorings/{monitoring_id}/posts/{post_id}',
             description='Monitoring Posts')
class PostResource(APIResource):

    @json_view(content_type='application/json',
               validators=(validate_post_data,),
               permission='create_post')
    def collection_post(self):
        """
        Post a post
        """
        monitoring = self.context
        post = self.request.validated['post']
        set_author(post, self.request, 'author')
        set_author(post.documents, self.request, 'author')
        upload_objects_documents(self.request, post)
        if post.author == get_monitoring_role('sas') and post.relatedPost is None:
            accelerator = get_monitoring_accelerator(self.context)
            post.dateOverdue = calculate_normalized_business_date(get_now(), POST_OVERDUE_TIME, accelerator, True)
        if monitoring.status in (ADDRESSED_STATUS, DECLINED_STATUS):
            post.postOf = CONCLUSION_OBJECT_TYPE
        monitoring.posts.append(post)
        if save_monitoring(self.request):
            self.LOGGER.info('Created monitoring post {}'.format(post.id),
                             extra=context_unpack(self.request,
                                                  {'MESSAGE_ID': 'monitoring_post_create'},
                                                  {'POST_ID': post.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                'Monitoring Post', monitoring_id=monitoring.id, post_id=post.id)
            return {'data': post.serialize('view')}

    @json_view(permission='view_monitoring')
    def collection_get(self):
        """
        List of posts
        """
        return {'data': [i.serialize('view') for i in self.context.posts]}

    @json_view(permission='view_monitoring')
    def get(self):
        """
        Retrieving the post
        """
        return {'data': self.context.serialize('view')}
