# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import json
from collections import Counter

import datetime
from django.contrib.auth.models import User
from django.db import transaction, connections
from django.db.models import Model, QuerySet
from django.db.models.query import RawQuerySet
from django.http import HttpRequest
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework.exceptions import ValidationError, NotFound
from typing import Callable, Any, Generator, List, Dict, cast, Optional, Tuple, Type, TypeVar

from skipper import settings
from skipper.core.utils.memoize import Memoize
from skipper.dataseries.models import data_point_event, ConsumerEventType, BulkInsertTaskData
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.contract.base import BaseDataPointModificationSerializer, BaseDataPointSerializer
from skipper.dataseries.storage.contract.factory import \
    get_data_point_serializer_for_data_series
from skipper.dataseries.storage.contract.view import BaseDataSeries_DataPointViewSet, StorageViewAdapter
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint, DisplayDataPoint
from skipper.dataseries.storage.dynamic_sql.queries.check_external_ids import check_external_ids
from skipper.dataseries.storage.dynamic_sql.queries.common import can_use_materialized_table
from skipper.dataseries.storage.dynamic_sql.queries.count import data_series_data_point_count
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.delete import delete_datapoint
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.dynamic_sql.queries.user_defined_filter import compute_user_defined_filter_for_raw_query
from skipper.dataseries.storage.dynamic_sql.serializers.display import display_data_point_serializer_class
from skipper.dataseries.storage.dynamic_sql.serializers.modification import DataPointModificationSerializer
from skipper.dataseries.storage.dynamic_sql.tasks.persist_data_point import persist_data_point_chunk, \
    async_persist_data_point_chunk
from skipper.dataseries.storage.static_ds_information import compute_data_series_query_info, \
    DataSeriesQueryInfo, data_point_serialization_keys
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.testing import SKIPPER_CELERY_TESTING
from skipper.core.lint import sql_cursor

__T = TypeVar('__T')
__U = TypeVar('__U')


def precompute_filter_part(
        external_ids: Optional[List[str]],
        filter_value: Dict[str, Any],
        data_series_query_info: DataSeriesQueryInfo,
        use_materialized_table: bool
) -> Tuple[str, Dict[str, Any], DataSeriesQueryInfo]:
    query_str = ''
    query_params: Dict[str, Any] = {}
    if external_ids is not None:
        # we can't ignore empty external_id query parameters to be in line with
        # drf default behaviour as this would be a security risk
        # where clients get more data than they anticipate
        complete_external_id_str = ""
        for i, external_id in enumerate(external_ids):
            complete_external_id_str = f"""
            {complete_external_id_str}
            {'OR' if i > 0 else ''} ds_dp.external_id = %(external_id_{str(i)})s
            """
            query_params[f'external_id_{str(i)}'] = external_id
        if len(complete_external_id_str) > 0:
            query_str = f"""
            {query_str}
            AND ({complete_external_id_str})
            """

    user_defined_filter = compute_user_defined_filter_for_raw_query(
        data_series_query_info=data_series_query_info,
        filter_params=filter_value,
        use_materialized_table=use_materialized_table
    )
    query_str = f"""
    {query_str}
    {user_defined_filter.filter_query_str}
    """
    query_params.update(user_defined_filter.query_params)

    return query_str, query_params, user_defined_filter.used_data_series_children


def raw_display_data_point_query(
        filter_value: Dict[str, Any],
        data_series: DataSeries,
        external_id_as_dimension_identifier: bool,
        external_ids: Optional[List[str]],
        point_in_time: Optional[datetime.datetime],
        changes_since: Optional[datetime.datetime],
        should_include_versions: bool,
        data_series_query_info: DataSeriesQueryInfo,
        data_point_id: Optional[str] = None,
        start_object: Optional[str] = None,
        reverse: bool = False,
        limit: Optional[int] = None,
) -> RawQuerySet:  # type: ignore
    data_series_obj: DataSeries = data_series

    query_params: Dict[str, Any] = {select_info.payload_variable_name: select_info.unescaped_display_id for
                                    select_info in
                                    select_infos(data_series_query_info)}

    filter_query_str = ''

    if data_point_id is not None:
        filter_query_str = f"""
        {filter_query_str}
        AND ds_dp.id = %(data_point_lookup_id)s
        """
        query_params['data_point_lookup_id'] = data_point_id

    use_materialized_table = can_use_materialized_table(data_series_query_info, point_in_time is not None)

    pagination_operator = '>='
    if reverse:
        pagination_operator = '<='

    if start_object is not None:
        try:
            page_start = json.loads(start_object)
        except ValueError:
            raise ValidationError('could not parse last query parameter. Is it valid json?')

        if 'id' not in page_start:
            raise ValidationError('id was not part of last query parameter!')

        if use_materialized_table:
            if 'inserted_at' not in page_start:
                raise ValidationError('inserted_at was not part of last query parameter!')

            filter_query_str = f"""
            {filter_query_str}
            AND (ds_dp.inserted_at, ds_dp.id) {pagination_operator} (%(inserted_at)s, %(start_id)s)
            """
            query_params['inserted_at'] = page_start['inserted_at']
            query_params['start_id'] = page_start['id']
        else:
            filter_query_str = f"""
            {filter_query_str}
            AND ds_dp.id {pagination_operator} %(start_id)s
            """
            query_params['start_id'] = page_start['id']

    precomputed_filter_query_part, filter_query_params, _ = precompute_filter_part(
        filter_value=filter_value,
        external_ids=external_ids,
        data_series_query_info=data_series_query_info,
        use_materialized_table=use_materialized_table
    )
    filter_query_str = f"""
    {filter_query_str}
    {precomputed_filter_query_part}
"""
    query_params.update(filter_query_params)

    # if we are ordering by something else than ds_dp.id
    # we have to do the offset calculation differently:
    # 1. find the values that the last id had,
    # 2. and do >= starting from there
    # but always break equality by ordering by ds_dp.id as well (but as the last one)

    order_columns = ['ds_dp.id']

    if use_materialized_table:
        order_columns.insert(0, 'ds_dp.inserted_at')

    if reverse:
        filter_query_str = f"""
        {filter_query_str}
        ORDER BY {' DESC,'.join(order_columns)} DESC
        """
    else:
        filter_query_str = f"""
        {filter_query_str}
        ORDER BY {' ASC, '.join(order_columns)} ASC
        """

    if limit is not None:
        filter_query_str = f"""
        {filter_query_str}
        LIMIT %(limit)s
        """
        query_params['limit'] = limit

    is_point_in_time = False
    if point_in_time is not None:
        is_point_in_time = True
        query_params['point_in_time'] = point_in_time

    is_changes_since = False
    if changes_since is not None:
        is_changes_since = True
        query_params['changes_since'] = changes_since

    query_str = data_series_as_sql_table(
        data_series=data_series_obj,
        payload_as_json=True,
        point_in_time=is_point_in_time,
        changes_since=is_changes_since,
        include_versions=should_include_versions,
        filter_str=filter_query_str,
        resolve_dimension_external_ids=external_id_as_dimension_identifier,
        data_series_query_info=data_series_query_info
    )

    print(query_str)
    
    raw = DisplayDataPoint.objects\
        .raw(
            query_str,
            query_params
        )

    return raw


class DynamicStorageViewAdapter(StorageViewAdapter):
    data_series_query_info: Memoize[
        DataSeries, DataSeriesQueryInfo]

    def __init__(self) -> None:
        self.data_series_query_info = Memoize(compute_data_series_query_info)

    def access_object(
            self,
            view: BaseDataSeries_DataPointViewSet,
            data_point_id: str,
            stub_enough: bool
    ) -> Any:
        if stub_enough and \
                (
                        view.access_data_series().backend != StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value
                    and view.access_data_series().backend != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value
                ):
            # all those methods need the current version, and do not really need the fully fetched variant
            qs = DataPoint.objects\
                .filter(
                    data_series_id=view.access_data_series().id,
                    id=data_point_id
                )
            if len(qs) == 0:
                raise NotFound()

            obj = qs[0]
            return obj

        raw_query = raw_display_data_point_query(
            data_point_id=data_point_id,
            filter_value=view.get_filter_value(),
            data_series=view.access_data_series(),
            external_ids=view.get_external_ids(),
            point_in_time=view.get_point_in_time(),
            changes_since=view.get_changes_since(),
            should_include_versions=view.should_include_versions(),
            external_id_as_dimension_identifier=view.external_id_as_dimension_identifier(),
            data_series_query_info=self.data_series_query_info(view.access_data_series())
        )
        if len(raw_query) == 0:
            raise NotFound()

        obj = raw_query[0]
        return obj

    def destroy_object(
            self,
            user_id: str,
            data_series_id: str,
            data_series_external_id: str,
            data_series_backend: str,
            record_source: str,
            instance: Model,
            view: BaseDataSeries_DataPointViewSet
    ) -> None:
        point_in_time: datetime.datetime = dbtime.now()
        sub_clock = dbtime.dp_sub_clock(get_current_tenant())
        instance_: DataPoint = cast(DataPoint, instance)
        if data_series_backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value or \
            data_series_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            delete_datapoint(
                get_current_tenant(),
                str(data_series_id),
                data_series_external_id,
                data_series_backend,
                instance_.id,
                instance_.external_id,
                point_in_time,
                sub_clock=sub_clock,
                record_source=record_source,
                user_id=user_id,
                data_point_serialization_keys=data_point_serialization_keys(
                    self.data_series_query_info(view.access_data_series())
                )
            )

        data_point_event(
            tenant=get_current_tenant(),
            point_in_time=point_in_time,
            data_series_id=data_series_id,
            payload={
                'data_series': {
                    'id': data_series_id,
                    'external_id': data_series_external_id
                },
                'data_points': [{
                    'id': instance_.id,
                    'external_id': instance_.external_id
                }]
            },
            event_type=ConsumerEventType.DATA_POINT_DELETED,
            sub_clock=sub_clock
        )

    def get_empty_queryset(
            self
    ) -> 'QuerySet[DataPoint]':
        # we do everything manually
        return DataPoint.objects.none()

    def encode_last_id_for_pagination(self, view: BaseDataSeries_DataPointViewSet, db_object: DisplayDataPoint) -> str:
        return json.dumps(db_object.pagination_data, sort_keys=True)

    def get_next_page_query_for_pagination(self, view: BaseDataSeries_DataPointViewSet, last_query: str, limit: int,
                                           request: HttpRequest) -> RawQuerySet:  # type: ignore
        return raw_display_data_point_query(
            start_object=last_query,
            limit=limit,
            filter_value=view.get_filter_value(),
            data_series=view.access_data_series(),
            point_in_time=view.get_point_in_time(),
            changes_since=view.get_changes_since(),
            should_include_versions=view.should_include_versions(),
            external_ids=view.get_external_ids(),
            external_id_as_dimension_identifier=view.external_id_as_dimension_identifier(),
            data_series_query_info=self.data_series_query_info(view.access_data_series())
        )

    def get_prev_page_query_for_pagination(
            self,
            view: BaseDataSeries_DataPointViewSet,
            last_query: str,
            limit: int,
            request: HttpRequest
    ) -> Optional[RawQuerySet]:  # type: ignore
        # FIXME: this could be a simpler query without as many joins
        return raw_display_data_point_query(
            start_object=last_query,
            reverse=True,
            limit=limit,
            filter_value=view.get_filter_value(),
            data_series=view.access_data_series(),
            point_in_time=view.get_point_in_time(),
            changes_since=view.get_changes_since(),
            should_include_versions=view.should_include_versions(),
            external_ids=view.get_external_ids(),
            external_id_as_dimension_identifier=view.external_id_as_dimension_identifier(),
            data_series_query_info=self.data_series_query_info(view.access_data_series())
        )

    def data_point_count(
            self,
            view: BaseDataSeries_DataPointViewSet
    ) -> int:
        data_series: DataSeries = view.access_data_series()
        pit = view.get_point_in_time()
        changes_since = view.get_changes_since()
        query_params = {
            'point_in_time': pit,
            'changes_since': changes_since
        }

        _query_info = self.data_series_query_info(data_series)

        use_materialized_table = can_use_materialized_table(_query_info, pit is not None)

        filter_query_part, filter_query_params, used_data_series_children = precompute_filter_part(
            filter_value=view.get_filter_value(),
            external_ids=view.get_external_ids(),
            data_series_query_info=self.data_series_query_info(data_series),
            use_materialized_table=use_materialized_table
        )

        query_params.update(filter_query_params)

        count_query = data_series_data_point_count(
            data_series=data_series,
            point_in_time=pit is not None,
            changes_since=changes_since is not None,
            used_data_series_children=used_data_series_children,
            filter_str=filter_query_part
        )
        with transaction.atomic():
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                cursor.execute(count_query, query_params)
                return cast(int, cursor.fetchone()[0])

    def get_serializer_class_for_update(
            self,
            should_include_versions: bool,
            point_in_time: Optional[datetime.datetime],
            data_series: DataSeries,
            partial: bool
    ) -> Type[BaseDataPointModificationSerializer]:
        return get_data_point_serializer_for_data_series(
            actual_class=DataPointModificationSerializer,
            data_series_id=str(data_series.id),
            update=True,
            patch=partial,
            point_in_time=point_in_time,
            should_include_versions=should_include_versions,
            data_series_query_info=self.data_series_query_info(data_series)
        )

    def get_serializer_class_for_display(
            self,
            should_include_versions: bool,
            data_series: DataSeries
    ) -> Type[BaseDataPointSerializer]:
        return display_data_point_serializer_class(
            include_versions=should_include_versions,
            data_series_children_query_info=self.data_series_query_info(data_series)
        )

    def get_serializer_class(
            self,
            should_include_versions: bool,
            point_in_time: Optional[datetime.datetime],
            data_series: DataSeries
    ) -> Type[BaseDataPointModificationSerializer]:
        # we can never update in this view
        return get_data_point_serializer_for_data_series(
            actual_class=DataPointModificationSerializer,
            data_series_id=str(data_series.id),
            update=False,
            point_in_time=point_in_time,
            should_include_versions=should_include_versions,
            data_series_query_info=self.data_series_query_info(data_series)
        )

    def create_bulk(
            self,
            view: BaseDataSeries_DataPointViewSet,
            point_in_time_timestamp: float,
            user_id: str,
            record_source: str,
            batch: List[Dict[str, Any]],
            asynchronous: bool,
            sub_clock: int
    ) -> List[str]:
        with transaction.atomic(using=settings.DATA_SERIES_DYNAMIC_SQL_DB_BULK):
            data_series_obj = view.access_data_series()

            task_data_ids: List[int] = []

            point_in_time: Optional[datetime.datetime] = view.get_point_in_time()

            serializer_class = get_data_point_serializer_for_data_series(
                actual_class=DataPointModificationSerializer,
                data_series_id=str(data_series_obj.id),
                update=True,
                point_in_time=point_in_time,
                should_include_versions=view.should_include_versions(),
                data_series_query_info=self.data_series_query_info(view.access_data_series())
            )
            serializer = serializer_class(
                data=batch,
                context=view.get_serializer_context(),
                many=True,
                bulk_insert=True
            )

            valid = serializer.is_valid(raise_exception=False)
            if not valid:
                # HACK: set this to None here, so that DRF does not
                # try to render anything and then fail
                serializer.initial_data = None
                raise ValidationError(serializer.errors)

            validated_datas = serializer.validated_data

            _duplicated_external_ids: List[str] = \
                [k for k, v in Counter(cast('List[str]', map(lambda x: x['external_id'], validated_datas))).items()
                 if v > 1]
            if len(_duplicated_external_ids) > 0:
                raise ValidationError('the following external_ids were duplicated in this batch: [' +
                                      ','.join(_duplicated_external_ids) + ']')

            if len(validated_datas) > settings.SKIPPER_DATA_SERIES_BULK_TASK_SIZE:
                raise ValidationError(f'number of datapoints in request exceed limit of {settings.SKIPPER_DATA_SERIES_BULK_TASK_SIZE}')

            created_external_ids = []
            list_chunk = []
            for elem in validated_datas:
                list_chunk.append(elem)
                _external_id = elem['external_id']
                created_external_ids.append(_external_id)

            if asynchronous:
                # first store the async data
                task_data = BulkInsertTaskData.objects.create(
                    tenant=data_series_obj.tenant,
                    data_series=data_series_obj,
                    point_in_time=datetime.datetime.fromtimestamp(point_in_time_timestamp, tz=datetime.timezone.utc),
                    # contains validated data and the serialization keys
                    data={
                        'validated_datas': list_chunk,
                        # hack, to ensure the serialization keys are not UUID objects anymore
                        'serialization_keys': serializer_class.serialization_keys
                    },
                    user=User.objects.get(id=user_id),
                    record_source=record_source,
                    sub_clock=sub_clock
                )
                if SKIPPER_CELERY_TESTING:
                    # when testing, immediately run the code,
                    # as we are in the same transaction always
                    async_persist_data_point_chunk.delay(
                        task_data_reference_id=task_data.id
                    )
                else:
                    # in production, we need to do this on transaction commit
                    # as otherwise the data would not be found in the celery task
                    # if it is launched immediately
                    task_data_ids.append(task_data.id)
            else:
                persist_data_point_chunk(
                    tenant_id=get_current_tenant().id,
                    tenant_name=get_current_tenant().name,
                    data_series_id=str(data_series_obj.id),
                    data_series_external_id=data_series_obj.external_id,
                    data_series_backend=data_series_obj.backend,
                    validated_datas=list_chunk,
                    serialization_keys=serializer_class.serialization_keys,
                    point_in_time_timestamp=point_in_time_timestamp,
                    user_id=user_id,
                    record_source=record_source,
                    sub_clock=sub_clock
                )

            # spawn the celery task after the transaction commits
            # this is to ensure the task exists
            # There is a slight possibility that data
            # might not be written because of a lost task
            # but for that we have healthchecks
            transaction.on_commit(
               lambda: [async_persist_data_point_chunk.delay(
                   task_data_reference_id=tsk_id
               ) for tsk_id in task_data_ids],
               using=settings.DATA_SERIES_DYNAMIC_SQL_DB_BULK
            )

            return created_external_ids

    def check_external_ids(self, view: BaseDataSeries_DataPointViewSet, external_ids: List[str]) -> List[str]:
        return check_external_ids(
            external_ids=external_ids,
            backend=view.access_data_series().backend,
            data_series_id=str(view.access_data_series().id),
            data_series_query_info=compute_data_series_query_info(view.access_data_series())
        )


adapter = DynamicStorageViewAdapter
