from openprocurement.api.utils import (
    context_unpack,
    decrypt,
    encrypt,
    get_now,
    generate_id,
    json_view,
    error_handler
)

from openprocurement.audit.api.constraints import MONITORING_TIME, ELIMINATION_PERIOD_TIME, \
    ELIMINATION_PERIOD_NO_VIOLATIONS_TIME
from openprocurement.audit.api.utils import (
    save_monitor,
    monitor_serialize,
    apply_patch,
    op_resource,
    APIResource,
    generate_monitor_id,
    generate_period,
    set_ownership
)
from openprocurement.audit.api.design import (
    monitors_real_by_dateModified_view,
    monitors_test_by_dateModified_view,
    monitors_by_dateModified_view,
    monitors_real_by_local_seq_view,
    monitors_test_by_local_seq_view,
    monitors_by_local_seq_view,
    monitors_by_status_dateModified_view,
    monitors_real_by_status_dateModified_view,
    monitors_test_by_status_dateModified_view,
)
from openprocurement.audit.api.validation import (
    validate_monitor_data,
    validate_patch_monitor_data,
    validate_patch_monitor_status,
    validate_credentials_generate
)
from openprocurement.audit.api.design import FIELDS
from functools import partial
from logging import getLogger

LOGGER = getLogger(__name__)

VIEW_MAP = {
    u'': monitors_real_by_dateModified_view,
    u'test': monitors_test_by_dateModified_view,
    u'_all_': monitors_by_dateModified_view,
}
STATUS_VIEW_MAP = {
    u'': monitors_real_by_status_dateModified_view,
    u'test': monitors_test_by_status_dateModified_view,
    u'_all_': monitors_by_status_dateModified_view,
}
CHANGES_VIEW_MAP = {
    u'': monitors_real_by_local_seq_view,
    u'test': monitors_test_by_local_seq_view,
    u'_all_': monitors_by_local_seq_view,
}
FEED = {
    u'dateModified': VIEW_MAP,
    u'changes': CHANGES_VIEW_MAP,
    u'status': STATUS_VIEW_MAP,
}


@op_resource(name='Monitors', path='/monitors')
class MonitorsResource(APIResource):

    def __init__(self, request, context):
        super(MonitorsResource, self).__init__(request, context)

        self.VIEW_MAP = VIEW_MAP
        self.STATUS_VIEW_MAP = STATUS_VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = monitor_serialize
        self.object_name_for_listing = 'Monitors'
        self.log_message_id = 'monitor_list_custom'

        self.feed_params = {}
        self.paging_params = {}
        self.feed_map = None

    def init_feed_params(self):
        status_filter = self.request.params.get('status')
        feed = "status" if status_filter else self.request.params.get('feed', '')

        fields = self.request.params.get('opt_fields', '')
        fields = fields.split(',') if fields else []

        limit = self.request.params.get('limit', '')
        if limit.isdigit() and (100 if fields else 1000) >= int(limit) > 0:
            limit = int(limit)
        else:
            limit = 1000
        self.feed_params.update(
            feed=feed,
            status=status_filter,
            mode=self.request.params.get('mode', ''),
            descending=bool(self.request.params.get('descending')),
            opt_fields=fields,
            limit=limit,
            status_filter=status_filter,
        )
        self.feed_map = self.FEED.get(feed, self.VIEW_MAP)

        try:
            skip = int(self.request.params.get('skip', '0'))
        except ValueError:
            skip = 0

        self.paging_params.update(
            offset=self.decrypt_offset(self.request.params.get('offset')),
            offset_doc_id=self.request.params.get('offset_doc_id'),
            prev_offset=self.decrypt_offset(self.request.params.get('prev_offset')),
            prev_offset_doc_id=self.request.params.get('prev_offset_doc_id'),
            skip=skip,
        )

    def decrypt_offset(self, offset):
        if offset:
            if self.feed_map is self.CHANGES_VIEW_MAP:
                decrypted_value = decrypt(self.server.uuid, self.db.name, offset)

                if decrypted_value and decrypted_value.isdigit():
                    offset = int(decrypted_value)
                else:
                    self.request.errors.add('params', 'offset', 'Offset expired/invalid')
                    self.request.errors.status = 404
                    raise error_handler(self.request.errors)

            elif self.feed_map is self.STATUS_VIEW_MAP:
                offset = offset.split(",")
        return offset

    def format_data(self, view):
        fields = self.feed_params["opt_fields"]
        all_fields = fields + ['dateModified', 'id']
        feed_map = self.feed_map

        kwargs = {}
        if fields:
            if set(fields).issubset(set(self.FIELDS)):
                if feed_map is self.CHANGES_VIEW_MAP:
                    def serialize(x):
                        r = {
                            i: j
                            for i, j in x.value.items() + [('id', x.id)]
                            if i in all_fields
                        }
                        return r

                elif feed_map is self.STATUS_VIEW_MAP:
                    def serialize(x):
                        r = {
                            i: j
                            for i, j in x.value.items() + [('id', x.id), ('dateModified', x.key[1])]
                            if i in all_fields
                        }
                        return r
                else:
                    def serialize(x):
                        r = {
                            i: j
                            for i, j in x.value.items() + [('id', x.id), ('dateModified', x.key)]
                            if i in all_fields
                        }
                        return r
            else:
                self.LOGGER.info(
                    'Used custom fields for {} list: {}'.format(self.object_name_for_listing, ','.join(sorted(fields))),
                    extra=context_unpack(self.request, {'MESSAGE_ID': self.log_message_id}))
                kwargs["include_docs"] = True

                serialize_func, request = self.serialize_func, self.request

                def serialize(x):
                    r = serialize_func(request, x[u'doc'], all_fields)
                    return r
        else:
            if feed_map is self.CHANGES_VIEW_MAP:
                def serialize(i):
                    return {'id': i.id, 'dateModified': i.value['dateModified']}
            elif feed_map is self.STATUS_VIEW_MAP:
                def serialize(i):
                    return {'id': i.id, 'dateModified': i.key[1]}
            else:
                def serialize(i):
                    return {'id': i.id, 'dateModified': i.key}
        results = [
            (serialize(o), o.key, o.id)
            for o in view(**kwargs)
        ]
        return results

    def format_result(self, view):
        data = {}
        results = self.format_data(view)

        next_params = None
        limit = self.feed_params["limit"]
        if len(results) > limit:
            next_item = results.pop(limit)
            next_params = self.get_link_query_params(
                offset=next_item[1], offset_doc_id=next_item[2],
                prev_offset=results[0][1], prev_offset_doc_id=results[0][2],
            )
        elif results:
            last_item = results[-1]
            next_params = self.get_link_query_params(
                offset=last_item[1], offset_doc_id=last_item[2],
                prev_offset=results[0][1], prev_offset_doc_id=results[0][2],
                skip=1,
            )
        elif self.paging_params["offset"]:
            next_param_kwargs = dict(
                offset=self.paging_params["offset"], skip=1,
            )
            if self.paging_params["offset_doc_id"]:
                next_param_kwargs.update(
                    offset_doc_id=self.paging_params["offset_doc_id"]
                )
            if self.paging_params["prev_offset"]:
                next_param_kwargs.update(
                    prev_offset=self.paging_params["prev_offset"],
                )
                if self.paging_params["prev_offset_doc_id"]:
                    next_param_kwargs.update(
                        prev_offset_doc_id=self.paging_params["prev_offset_doc_id"],
                    )
            next_params = self.get_link_query_params(**next_param_kwargs)

        if next_params:
            data["next_page"] = {
                "offset": next_params['offset'],
                "path": self.request.route_path(self.object_name_for_listing, _query=next_params),
                "uri": self.request.route_url(self.object_name_for_listing, _query=next_params)
            }

        data['data'] = [i[0] for i in results]

        prev_offset = prev_offset_doc_id = None
        if self.paging_params["prev_offset"]:
            prev_offset = self.paging_params["prev_offset"]
            if self.paging_params["prev_offset_doc_id"]:
                prev_offset_doc_id = self.paging_params["prev_offset_doc_id"]

        elif self.paging_params["offset"]:
            prev_param_kwargs = dict(
                startkey=self.paging_params["offset"],
                limit=limit + 1, skip=limit, descending=not self.feed_params["descending"]
            )
            if self.paging_params.get("offset_doc_id") is not None:
                prev_param_kwargs.update(startkey_docid=self.paging_params.get("offset_doc_id"))
            view = self.get_feed_view(**prev_param_kwargs)
            prev_items = list(view())

            if prev_items:
                prev_offset, prev_offset_doc_id = prev_items[0].key, prev_items[0].id

        if prev_offset:
            prev_params = self.get_link_query_params(
                offset=prev_offset,
                offset_doc_id=prev_offset_doc_id,
            )
            data['prev_page'] = {
                "offset": prev_params['offset'],
                "path": self.request.route_path(self.object_name_for_listing, _query=prev_params),
                "uri": self.request.route_url(self.object_name_for_listing, _query=prev_params)
            }

        return data

    def get_link_query_params(self, **q_params):
        q_params.update(self.feed_params)
        q_params = {k: v for k, v in q_params.items() if v not in (None, '')}

        if self.feed_map is self.CHANGES_VIEW_MAP:
            q_params['offset'] = encrypt(self.server.uuid, self.db.name, q_params['offset'])

            if q_params.get('prev_offset'):
                q_params['prev_offset'] = encrypt(self.server.uuid, self.db.name, q_params['prev_offset'])

            for k in ("offset_doc_id", "prev_offset_doc_id"):
                if k in q_params:
                    del q_params[k]

        elif self.feed_map is self.STATUS_VIEW_MAP:
            q_params['offset'] = ",".join(q_params['offset'])

            if q_params.get('prev_offset'):
                q_params['prev_offset'] = ",".join(q_params['prev_offset'])

        if q_params["opt_fields"]:
            q_params["opt_fields"] = ",".join(q_params["opt_fields"])
        else:
            del q_params["opt_fields"]

        if not q_params["descending"]:
            del q_params["descending"]

        return q_params

    def get_feed_view(self, **kwargs):
        feed_view = self.feed_map.get(self.feed_params["mode"], self.feed_map[u''])
        if self.feed_params["status_filter"]:
            if kwargs.get("descending"):
                default_start, default_end = {}, None
            else:
                default_start, default_end = None, {}

            start = kwargs["startkey"][1] if kwargs.get("startkey") else default_start
            kwargs["startkey"] = [self.feed_params["status_filter"], start]
            kwargs["endkey"] = [self.feed_params["status_filter"], default_end]

        view = partial(feed_view, self.db, **kwargs)
        return view

    @json_view(permission='view_listing')
    def get(self):
        self.init_feed_params()

        view_kwargs = dict(
            limit=self.feed_params["limit"] + 1,
            descending=self.feed_params["descending"],
            skip=self.paging_params["skip"],
        )
        if self.paging_params["offset"]:
            view_kwargs.update(startkey=self.paging_params["offset"])

        if self.paging_params["offset_doc_id"]:
            view_kwargs.update(startkey_docid=self.paging_params["offset_doc_id"])

        if self.update_after:
            view_kwargs["stale"] = 'update_after'

        view = self.get_feed_view(**view_kwargs)

        return self.format_result(view)

    @json_view(content_type='application/json',
               permission='create_monitor',
               validators=(validate_monitor_data,))
    def post(self):
        monitor = self.request.validated['monitor']
        monitor.id = generate_id()
        monitor.monitoring_id = generate_monitor_id(get_now(), self.db, self.server_id)
        monitor.dateModified = monitor.dateCreated
        save_monitor(self.request)
        LOGGER.info('Created monitor {}'.format(monitor.id),
                    extra=context_unpack(self.request,
                                         {'MESSAGE_ID': 'monitor_create'},
                                         {'MONITOR_ID': monitor.id}))
        self.request.response.status = 201
        self.request.response.headers['Location'] = self.request.route_url('Monitor', monitor_id=monitor.id)
        return {'data': monitor.serialize('view')}


@op_resource(name='Monitor', path='/monitors/{monitor_id}')
class MonitorResource(APIResource):

    @json_view(permission='view_monitor')
    def get(self):
        monitor = self.request.validated['monitor']
        return {'data': monitor.serialize('view')}

    @json_view(content_type='application/json',
               validators=(validate_patch_monitor_data, validate_patch_monitor_status),
               permission='edit_monitor')
    def patch(self):
        monitor = self.request.validated['monitor']
        monitor_old_status = monitor.status

        apply_patch(self.request, save=False, src=self.request.validated['monitor_src'])

        monitor.dateModified = get_now()
        if monitor_old_status == 'draft' and monitor.status == 'active':
            monitor.monitoringPeriod = generate_period(monitor.dateModified, MONITORING_TIME)
            monitor.decision.datePublished = monitor.dateModified
        elif monitor_old_status == 'active' and monitor.status == 'addressed':
            monitor.conclusion.datePublished = monitor.dateModified
            monitor.eliminationPeriod = generate_period(monitor.dateModified, ELIMINATION_PERIOD_TIME)
        elif monitor_old_status == 'active' and monitor.status == 'declined':
            monitor.eliminationPeriod = generate_period(monitor.dateModified, ELIMINATION_PERIOD_NO_VIOLATIONS_TIME)
            monitor.conclusion.datePublished = monitor.dateModified
        elif monitor_old_status == 'addressed' and monitor.status == 'completed':
            monitor.eliminationReport.datePublished = monitor.dateModified
            monitor.eliminationReport.eliminationResolution = monitor.dateModified
        elif monitor_old_status == 'active' and monitor.status == 'stopped':
            monitor.stopping.datePublished = monitor.dateModified

        save_monitor(self.request)
        LOGGER.info('Updated monitor {}'.format(monitor.id),
                    extra=context_unpack(self.request, {'MESSAGE_ID': 'monitor_patch'}))
        return {'data': monitor.serialize('view')}


@op_resource(name='Monitor credentials',
             path='/monitors/{monitor_id}/credentials',
             description="Monitor credentials")
class MonitorCredentialsResource(APIResource):
    @json_view(permission='generate_credentials', validators=(validate_credentials_generate,))
    def patch(self):
        monitor = self.request.validated['monitor']

        set_ownership(monitor, self.request, 'tender_owner')
        if save_monitor(self.request):
            self.LOGGER.info('Generate Monitor credentials {}'.format(monitor.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'monitor_patch'}))
            return {
                'data': monitor.serialize('view'),
                'access': {
                    'token': monitor.tender_owner_token
                }
            }
