from logging import getLogger

from openprocurement.audit.api.utils import APIResource, json_view, context_unpack
from openprocurement.audit.inspection.design import (
    inspections_by_monitoring_id_view,
    test_inspections_by_monitoring_id_view,
    CHANGES_FIELDS,
)
from openprocurement.audit.inspection.utils import (
    inspection_serialize,
    op_resource,
)

LOGGER = getLogger(__name__)


@op_resource(name='Monitoring inspections', path='/monitorings/{monitoring_id}/inspections')
class MonitoringInspectionsResource(APIResource):

    @json_view(permission='view_listing')
    def get(self):
        monitoring_id = self.request.matchdict["monitoring_id"]

        opt_fields = self.request.params.get('opt_fields', '')
        opt_fields = set(e for e in opt_fields.split(',') if e)

        mode = self.request.params.get('mode', '')
        views = {
            "": inspections_by_monitoring_id_view,
            "test": test_inspections_by_monitoring_id_view,
        }
        list_view = views.get(mode, inspections_by_monitoring_id_view)

        view_kwargs = dict(
            limit=500,  # TODO: pagination
            startkey=[monitoring_id, None],
            endkey=[monitoring_id, {}],
        )
        default_fields = set(CHANGES_FIELDS) | {"id", "dateCreated"}
        if opt_fields - default_fields:
            self.LOGGER.info(
                'Used custom fields for monitoring list: {}'.format(','.join(sorted(opt_fields))),
                extra=context_unpack(self.request, {'MESSAGE_ID': "CUSTOM_MONITORING_LIST"}))

            results = [
                inspection_serialize(self.request, i[u'doc'], opt_fields | default_fields)
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
