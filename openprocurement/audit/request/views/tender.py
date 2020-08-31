from logging import getLogger

from openprocurement.audit.api.utils import (
    APIResource,
    context_unpack,
    op_resource,
    json_view
)
from openprocurement.audit.request.design import (
    CHANGES_FIELDS,
    requests_real_by_tender_id_view,
    requests_test_by_tender_id_view,
    requests_by_tender_id_view,
)
from openprocurement.audit.request.utils import request_serialize, op_resource

LOGGER = getLogger(__name__)


@op_resource(name='Tender Requests', path='/tenders/{tender_id}/requests')
class TenderRequestResource(APIResource):

    def __init__(self, request, context):
        super(TenderRequestResource, self).__init__(request, context)
        self.views = {
            "": requests_real_by_tender_id_view,
            "test": requests_test_by_tender_id_view,
            "_all_": requests_by_tender_id_view,
        }
        self.default_fields = set(CHANGES_FIELDS) | {"id", "dateCreated"}

    @json_view(permission='view_listing')
    def get(self):
        tender_id = self.request.matchdict["tender_id"]

        opt_fields = self.request.params.get('opt_fields', '')
        opt_fields = set(e for e in opt_fields.split(',') if e)

        mode = self.request.params.get('mode', '')
        list_view = self.views.get(mode, "")

        view_kwargs = dict(
            limit=500,  # TODO: pagination
            startkey=[tender_id, None],
            endkey=[tender_id, {}],
        )

        if opt_fields - self.default_fields:
            self.LOGGER.info(
                'Used custom fields for requests list: {}'.format(','.join(sorted(opt_fields))),
                extra=context_unpack(self.request, {'MESSAGE_ID': "CUSTOM_REQUESTS_LIST"}))

            results = [
                request_serialize(self.request, i[u'doc'], opt_fields | self.default_fields)
                for i in list_view(self.db, include_docs=True, **view_kwargs)
            ]
        else:
            results = [
                dict(
                    id=e.id,
                    dateCreated=e.key[1],
                    **e.value
                )
                for e in list_view(self.db, **view_kwargs)
            ]

        data = {
            'data': results,
        }
        return data
