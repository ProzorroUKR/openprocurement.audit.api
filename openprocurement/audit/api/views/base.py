from openprocurement.audit.api.mask import mask_object_data
from openprocurement.audit.api.traversal import factory
from openprocurement.audit.api.utils import error_handler, parse_offset, raise_operation_error
from cornice.resource import resource, view
from functools import partial
from logging import getLogger


json_view = partial(view, renderer='simplejson')
op_resource = partial(resource, error_handler=error_handler, factory=factory)


class APIResource:
    def __init__(self, request, context):
        self.context = context
        self.request = request
        self.LOGGER = getLogger(type(self).__module__)

    def db_fields(self, fields):
        return fields


class MongodbResourceListing(APIResource):
    listing_name = "Items"
    offset_field = "public_modified"
    listing_default_fields = {"dateModified"}
    listing_allowed_fields = {"dateModified", "created", "modified"}
    default_limit = 100
    max_limit = 1000

    db_listing_method: callable
    filter_key = None

    @staticmethod
    def add_mode_filters(filters: dict, mode: str):
        if "test" in mode:
            filters["is_test"] = True
        elif "all" not in mode:
            filters["is_test"] = False

    @json_view(permission="view_listing")
    def get(self):
        params = {}
        filters = {}
        keys = {}

        # filter
        if self.filter_key:
            filter_value = self.request.matchdict[self.filter_key]
            filters[self.filter_key] = filter_value
            keys[self.filter_key] = filter_value

        # mode param
        mode = self.request.params.get("mode", "")
        if mode:
            params["mode"] = self.request.params.get("mode")
        self.add_mode_filters(filters, mode)

        # offset param
        offset = None
        offset_param = self.request.params.get("offset")
        if offset_param:
            try:
                offset = parse_offset(offset_param)
            except ValueError:
                raise_operation_error(
                    self.request, f"Invalid offset provided: {offset_param}",
                    status=404, location="querystring", name="offset"
                )
            params["offset"] = offset

        # limit param
        limit_param = self.request.params.get("limit")
        if limit_param:
            try:
                limit = int(limit_param)
            except ValueError as e:
                raise_operation_error(
                    self.request, e.args[0],
                    status=400, location="querystring", name="limit"
                )
            else:
                params["limit"] = min(limit, self.max_limit)

        # descending param
        if self.request.params.get("descending"):
            params["descending"] = 1

        # opt_fields param
        if self.request.params.get("opt_fields"):
            opt_fields = set(self.request.params.get("opt_fields", "").split(",")) & self.listing_allowed_fields
            filtered_fields = opt_fields - self.listing_default_fields
            if filtered_fields:
                params["opt_fields"] = ",".join(sorted(filtered_fields))
        else:
            opt_fields = set()

        # prev_page
        prev_params = dict(**params)
        if params.get("descending"):
            del prev_params["descending"]
        else:
            prev_params["descending"] = 1

        data_fields = opt_fields | self.listing_default_fields
        db_fields = self.db_fields(data_fields)

        # call db method
        results = self.db_listing_method(
            offset_field=self.offset_field,
            offset_value=offset,
            fields=db_fields,
            descending=params.get("descending"),
            limit=params.get("limit", self.default_limit),
            filters=filters,
        )

        # prepare response
        if results:
            params["offset"] = results[-1][self.offset_field]
            prev_params["offset"] = results[0][self.offset_field]
            if self.offset_field not in self.listing_allowed_fields:
                for r in results:
                    r.pop(self.offset_field)
        data = {
            "data": self.filter_results_fields(results, data_fields),
            "next_page": self.get_page(keys, params)
        }
        if self.request.params.get("descending") or self.request.params.get("offset"):
            data["prev_page"] = self.get_page(keys, prev_params)

        return data

    def get_page(self, keys, params):
        return {
            "offset": params.get("offset", ""),
            "path": self.request.route_path(self.listing_name, _query=params, **keys),
            "uri": self.request.route_url(self.listing_name, _query=params, **keys)
        }

    def filter_results_fields(self, results, fields):
        all_fields = fields | {"id"}
        for r in results:
            for k in list(r.keys()):
                if k not in all_fields:
                    del r[k]
        return results


class RestrictedResourceListingMixin:
    mask_mapping = {}
    request = None

    def db_fields(self, fields):
        fields = super().db_fields(fields)
        return fields | {"restricted"}

    def filter_results_fields(self, results, fields):
        for r in results:
            mask_object_data(self.request, r, mask_mapping=self.mask_mapping)
        results = super().filter_results_fields(results, fields)
        return results


DEFAULT_PAGE = 1
DEFAULT_LIMIT = 500
DEFAULT_DESCENDING = False


class APIResourcePaginatedListing(APIResource):
    sort_by: str = "dateCreated"
    db_listing_method: callable
    obj_id_key: str
    obj_id_key_filter: str
    serialize_method: callable
    default_fields: set

    @classmethod
    def serialize(cls, *args, **kwargs):
        if not cls.serialize_method:
            raise NotImplemented
        return cls.serialize_method(*args, **kwargs)

    @staticmethod
    def add_mode_filters(filters: dict, mode: str):
        if mode == "test":
            filters["is_test"] = True
        elif "all" not in mode:
            filters["is_test"] = False

    @json_view(permission='view_listing')
    def get(self):
        obj_id = self.request.matchdict[self.obj_id_key]
        filters = {
            self.obj_id_key_filter: obj_id,
        }

        opt_fields = self.request.params.get('opt_fields', '')
        opt_fields = set(e for e in opt_fields.split(',') if e)
        opt_fields |= self.default_fields

        mode = self.request.params.get('mode', '')
        self.add_mode_filters(filters, mode)

        descending = bool(self.request.params.get('descending', DEFAULT_DESCENDING))
        limit = int(self.request.params.get('limit', DEFAULT_LIMIT))
        page = int(self.request.params.get('page', DEFAULT_PAGE))
        skip = page * limit - limit

        db_fields = self.db_fields(opt_fields)

        results, total = self.db_listing_method(
            skip=skip,
            limit=limit,
            fields=db_fields,
            sort_by=self.sort_by,
            descending=descending,
            filters=filters,
        )
        data = {
            'data': [self.serialize_method(r, opt_fields) for r in results],
            'count': len(results),
            'page': page,
            'limit': limit,
            'total': total,
        }
        return data
