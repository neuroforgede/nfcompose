# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import json

from django.http import HttpRequest
from django.utils.safestring import SafeString
from rest_framework.exceptions import NotFound, APIException, ValidationError
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, ListModelMixin
from rest_framework.parsers import JSONParser
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet
from typing import List, Any, Sequence, Type, Optional, Iterable, Dict

from skipper.core.exceptions.http import Http400
from skipper.core.utils.memoize import Memoize
from skipper.core.views.mixin import HttpErrorAwareCreateModelMixin, HasTenantSetPermission
from skipper.dataseries import constants
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_DATA_POINT, DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.parsers.multipart import DataPointMultipartFormencodeParser
from skipper.dataseries.storage import views
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.contract.models import DisplayDataPoint
from skipper.dataseries.storage.contract.view import EmptySerializer, BaseDataSeries_DataPointViewSet, \
    StorageViewAdapter
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.views.common import HasDataSeriesGlobalReadPermission, get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.dataseries.views.datapoint.external_id import use_external_id_as_dimension_identifier
from skipper.dataseries.views.datapoint.point_in_time import PointInTimeMixin
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin, \
    CustomizableBrowsableAPIRenderer
from skipper.pagination import IdBasedPagination


def gen_DataSeries_DataPointViewSet(
        permission_key: str,
        base_name: str,
        _history: bool,
        view_display_name: str
) -> Type[BaseDataSeries_DataPointViewSet]:

    class Actual_DataSeries_DataPointViewSet(
        CustomizableBrowsableAPIRendererObjectMixin,
        PointInTimeMixin,
        RetrieveModelMixin,
        ListModelMixin,
        GenericViewSet,  # type: ignore
    ):
        # custom detail behaviour
        history = _history

        # allow all characters except /git 
        lookup_value_regex = '[^/]+'

        skipper_base_name = base_name

        renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]
        parser_classes = [JSONParser, DataPointMultipartFormencodeParser]

        pagination_class = IdBasedPagination

        # we are using hand written queries
        # so we can not filter
        filterset_class = None
        filterset_backends: List[Any] = []

        data_series_memo: Memoize[Any, Optional[DataSeries]]

        permission_classes: Sequence[Type[BasePermission]] = [
            HasTenantSetPermission,
            # we only need the global read permission for datapoints here
            # the rest is determined on a per object level basis in get_data_series_object
            HasDataSeriesGlobalReadPermission,
            get_dataseries_permissions_class(permission_key),
        ]

        _storage_view_adapter: Optional[StorageViewAdapter] = None

        def get_view_name(self) -> str:
            return view_display_name

        def __init__(self, **kwargs: Any):
            super().__init__()

            def _access_data_series(data: Any) -> Optional[DataSeries]:
                return get_data_series_object(self.kwargs, permission_key, self.request)

            self.data_series_memo = Memoize(_access_data_series)

        def access_data_series(self) -> DataSeries:
            _data_series: DataSeries = self.data_series_memo(())
            if _data_series is None:
                raise NotFound('dataseries not found')
            else:
                return _data_series

        def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
            if not StorageBackendType.from_string(self.access_data_series().backend).has_history() and _history:
                raise ValidationError({"error": f"data_series backend {self.access_data_series().backend} does not support history"})

            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)

            assert page is not None

            _serialized = self.storage_view_adapter().serialize_list(self, page)

            ret = self.get_paginated_response(_serialized)

            return ret

        def storage_view_adapter(self) -> StorageViewAdapter:
            if self._storage_view_adapter is None:
                self._storage_view_adapter = views.storage_view_adapter(self.access_data_series().get_backend_type())
            return self._storage_view_adapter

        def get_object(self) -> Any:
            if not StorageBackendType.from_string(self.access_data_series().backend).has_history() and _history:
                raise ValidationError({"error": f"data_series backend {self.access_data_series().backend} does not support history"})

            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

            assert lookup_url_kwarg in self.kwargs, (
                    'Expected view %s to be called with a URL keyword argument '
                    'named "%s". Fix your URL conf, or set the `.lookup_field` '
                    'attribute on the view correctly.' %
                    (self.__class__.__name__, lookup_url_kwarg)
            )

            data_point_id = self.kwargs[lookup_url_kwarg]
            by_external_id = 'by_external_id' in self.kwargs

            try:
                if by_external_id:
                    _external_id = data_point_id
                    _data_point_id = gen_uuid(data_series_id=self.access_data_series().id, external_id=data_point_id)
                else:
                    _data_point_id = data_point_id
                obj = self.storage_view_adapter().access_object(
                    self,
                    data_point_id=_data_point_id,
                    stub_enough=(
                            self.action == 'update' or
                            self.action == 'partial_update' or
                            self.action == 'destroy'
                    )
                )
            except NotFound:
                if by_external_id:
                    raise NotFound('did not find DataPoint with external_id ' + str(data_point_id))
                else:
                    raise NotFound('did not find DataPoint with id ' + str(data_point_id))

            # FIXME: has to be done differently for other backends that do not use django features
            # May raise a permission denied
            # object permissions have to be stored in the storage backend
            self.check_object_permissions(self.request, obj)

            return obj

        def get_next_page_query_for_pagination(self, last_query: str, limit: int,
                                               request: HttpRequest) -> Optional[Iterable[Any]]:
            return self.storage_view_adapter().get_next_page_query_for_pagination(self, last_query, limit, request)

        def get_prev_page_query_for_pagination(
                self,
                last_query: str,
                limit: int,
                request: HttpRequest
        ) -> Optional[Iterable[Any]]:
            if self.should_include_prev_page_for_pagination(request):
                return self.storage_view_adapter().get_prev_page_query_for_pagination(self, last_query, limit, request)
            return None

        def get_filter_value(self) -> Dict[str, Any]:
            filter_value: Dict[str, Any]
            if 'filter' in self.request.GET:
                try:
                    _filter_str = self.request.GET['filter']
                    if _filter_str != '':
                        filter_value = json.loads(_filter_str)
                    else:
                        filter_value = {}
                except:
                    raise ValidationError(f'filter {self.request.GET["filter"]} could not be parsed as valid json')
                if not isinstance(filter_value, dict):
                    raise ValidationError('filter in url parameters was no json object/dictionary')
            else:
                filter_value = {}
            return filter_value

        def get_external_ids(self) -> Optional[List[str]]:
            return self.request.GET.getlist('external_id') if 'external_id' in self.request.GET else None  # type: ignore

        def external_id_as_dimension_identifier(self) -> bool:
            return use_external_id_as_dimension_identifier(
                self.request.GET
            )

        def encode_last_id_for_pagination(self, db_object: Any) -> str:
            return self.storage_view_adapter().encode_last_id_for_pagination(
                self,
                db_object
            )

        def should_include_prev_page_for_pagination(
                self,
                request: HttpRequest
        ) -> bool:
            if 'include_prev' in request.GET:
                include_prev_val = request.GET['include_prev']
                if include_prev_val is None or include_prev_val == '' or include_prev_val == 'true':
                    return True
            return False

        def get_total_count_for_pagination(self, request: HttpRequest) -> Optional[int]:
            if 'count' in request.GET:
                cnt_query_val = request.GET['count']
                if cnt_query_val is None or cnt_query_val == '' or cnt_query_val == 'true':
                    return self.storage_view_adapter().data_point_count(self)
                return None
            else:
                return None

        def get_serializer_class(self) -> Type[Serializer[DisplayDataPoint]]:
            try:
                if self.action == 'destroy':
                    if self.action == 'DELETE':
                        return EmptySerializer
                if self.action == 'update' or self.action == 'partial_update':
                    # FIXME: this should not really require point_in_time
                    # but our api requires this for now
                    # clean this up!
                    return self.storage_view_adapter().get_serializer_class_for_update(
                        should_include_versions=self.should_include_versions(),
                        point_in_time=self.get_point_in_time(),
                        data_series=self.access_data_series(),
                        partial=(self.request.method == 'PATCH')
                    )
                if self.action == 'list' or self.action == 'retrieve':
                    return self.storage_view_adapter().get_serializer_class_for_display(
                        should_include_versions=self.should_include_versions(),
                        data_series=self.access_data_series()
                    )
                return self.storage_view_adapter().get_serializer_class(
                    should_include_versions=self.should_include_versions(),
                    point_in_time=self.get_point_in_time(),
                    data_series=self.access_data_series()
                )
            except APIException:
                return EmptySerializer

        def get_queryset(self) -> Any:
            return self.storage_view_adapter().get_empty_queryset()

        def get_description_string(self) -> str:
            doc_string: str
            base_doc_string = f"""
            Supported GET query parameters:
            <br>
            <br>
            - changes_since=&lt;timestamp&gt;<br>
            - filter={{"$or": [{{"&lt;dimension/fact external id&gt;": "&lt;some-value&gt;", ...}}, {{"&lt;dimension/fact external id&gt;": "&lt;some-other-value&gt;", ...}}]}}
                (supports logical operators $or, $and, $not and primitive operators $eq, $lt, $lte, $ne, $gte, $gt, $in, $nin, $prefix)<br>
            - count[=true] <br>
            - external_id=<str> (repeatable) <br>
            - identify_dimensions_by_external_id[=true] <br>
            """
            if _history:
                doc_string = f"""
                History View for datapoints with read-only access. <br><br>
                {base_doc_string}
                <br>
                - point_in_time=&lt;timestamp&gt;<br>
                - include_versions[=true]
                """
            else:
                doc_string = f"""
                CRUD View for datapoints. <br><br>
                {base_doc_string}
                """
            return SafeString(doc_string)

        def get_name_string(self) -> str:
            if 'pk' in self.kwargs:
                return f'{self.access_data_series().name} - {self.get_view_name()}: {self.get_object().external_id}'
            else:
                return f'{self.access_data_series().name} - {self.get_view_name()}s'

    if not _history:
        class WithModifications(
            HttpErrorAwareCreateModelMixin,
            UpdateModelMixin,
            DestroyModelMixin,
            Actual_DataSeries_DataPointViewSet
        ):
            def perform_destroy(self, instance: Any) -> None:
                self.storage_view_adapter().destroy_object(
                    user_id=str(self.request.user.id),
                    data_series_id=str(self.access_data_series().id),
                    data_series_external_id=self.access_data_series().external_id,
                    data_series_backend=self.access_data_series().backend,
                    record_source='REST API',
                    instance=instance,
                    view=self
                )

        return WithModifications
    else:
        class WithoutModifications(Actual_DataSeries_DataPointViewSet):
            pass

        return WithoutModifications


DataSeries_DataPointViewSet = gen_DataSeries_DataPointViewSet(
    DATASERIES_PERMISSION_KEY_DATA_POINT,
    constants.data_series_data_point_base_name,
    False,
    'Data Point'
)
history_DataSeries_DataPointViewSet = gen_DataSeries_DataPointViewSet(
    DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
    constants.data_series_history_data_point_base_name,
    True,
    "History (unstable API) - Data Point"
)

