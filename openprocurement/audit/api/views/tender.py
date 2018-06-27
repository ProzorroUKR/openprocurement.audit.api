from openprocurement.api.utils import json_view
from openprocurement.audit.api.utils import (
    op_resource,
    context_unpack,
    APIResource,
    monitoring_serialize,
)
from openprocurement.audit.api.design import (
    monitorings_by_tender_id_view,
    test_monitorings_by_tender_id_view,
    MONITORINGS_BY_TENDER_FIELDS,
)
from logging import getLogger

LOGGER = getLogger(__name__)


@op_resource(name='Tender Monitorings', path='/tenders/{tender_id}/monitorings')
class TenderMonitoringResource(APIResource):

    def __init__(self, request, context):
        super(TenderMonitoringResource, self).__init__(request, context)
        self.views = {
            "": monitorings_by_tender_id_view,
            "test": test_monitorings_by_tender_id_view,
        }
        self.default_fields = set(MONITORINGS_BY_TENDER_FIELDS) | {"id", "dateCreated"}

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
                'Used custom fields for monitoring list: {}'.format(','.join(sorted(opt_fields))),
                extra=context_unpack(self.request, {'MESSAGE_ID': "CUSTOM_MONITORING_LIST"}))

            results = [
                monitoring_serialize(self.request, i[u'doc'], opt_fields | self.default_fields)
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
