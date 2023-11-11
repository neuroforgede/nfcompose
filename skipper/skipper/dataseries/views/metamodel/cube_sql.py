# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import dataclasses

from django.db import transaction, connections
from django.db.models import QuerySet
from django.http import HttpResponse
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from typing import Any, Dict, cast

from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_CUBE_SQL
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.serializers.metamodel.data_series import DataSeriesViewCreationSerializer, \
    DataSeriesCubeSQLSerializer
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.static_ds_information import compute_data_series_query_info, \
    data_series_query_info_for_full_history
from skipper.dataseries.views.common import get_dataseries_permissions_class, HasDataSeriesGlobalReadPermission
from skipper.dataseries.views.contract import get_data_series_object
from skipper.dataseries.views.datapoint.external_id import use_external_id_as_dimension_identifier
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor
from skipper.dataseries.views.datapoint.point_in_time import PointInTimeMixin
from skipper.dataseries.storage.contract import StorageBackendType


def payload_as_json(request: Request) -> bool:
    if 'payload_as_json' in request.GET:
        payload_as_json = request.GET['payload_as_json']
        if payload_as_json is None or payload_as_json == '' or payload_as_json == 'true':
            return True
    return False


class DataSeriesCubeSQLView(
    GenericAPIView,  # type: ignore
    PointInTimeMixin):

    permission_classes = [
        *metamodel_base_line_permissions,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_CUBE_SQL)
    ]

    # enable history view features
    # this keyword is not nice, but this
    # properly enables usage of get_point_in_time and get_changes_since
    history = True

    def get_serializer_class(self) -> Any:
        return DataSeriesCubeSQLSerializer

    def get_queryset(self) -> QuerySet[DataSeries]:
        # check permission
        get_data_series_object(
            kwargs_object=self.kwargs,
            action=DATASERIES_PERMISSION_KEY_CUBE_SQL,
            request=self.request
        )
        return DataSeries.objects.none()

    def full_history(self) -> bool:
        if self.history and 'full_history' in self.request.GET:
            full_history = self.request.GET['full_history']
            if full_history is None or full_history == '' or full_history == 'true':
                return True
        return False

    def get(self, request: Request, **kwargs: str) -> HttpResponse:
        with transaction.atomic():
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                data_series = get_data_series_object(
                    kwargs_object=kwargs,
                    action=DATASERIES_PERMISSION_KEY_CUBE_SQL,
                    request=request
                )
                if data_series is None:
                    raise NotFound('data_series not found')

                point_in_time = self.get_point_in_time()
                changes_since = self.get_changes_since()
                should_include_versions = self.should_include_versions()
                full_history = self.full_history()

                if full_history and (should_include_versions or point_in_time is not None):
                    raise ValidationError({
                        'error': f'full_history and include_versions/point_in_time do not work together'
                    })

                if data_series.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value and (
                    should_include_versions or point_in_time is not None
                ):
                    raise ValidationError({
                        'error': f'data_series backend {data_series.backend} does not support history'
                    })

                if full_history and data_series.backend != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                    raise ValidationError({
                        'error': f'full_history is not supported on backend {data_series.backend}'
                    })

                data_series_query_info = compute_data_series_query_info(
                    data_series
                )

                if full_history:
                    data_series_query_info = data_series_query_info_for_full_history(
                        data_series_query_info,
                    )

                query_params: Dict[str, Any] = {select_info.payload_variable_name: select_info.unescaped_display_id for
                                                select_info in
                                                select_infos(data_series_query_info)}

                sql_template = data_series_as_sql_table(
                    data_series,
                    include_in_payload=None,
                    payload_as_json=payload_as_json(request),
                    resolve_dimension_external_ids=use_external_id_as_dimension_identifier(
                        cast(Dict[str, Any], request.GET)
                    ),
                    point_in_time=point_in_time is not None,
                    changes_since=changes_since is not None,
                    include_versions=should_include_versions,
                    data_series_query_info=data_series_query_info
                )

                if point_in_time is not None:
                    query_params['point_in_time'] = point_in_time
                
                if changes_since is not None:
                    query_params['changes_since'] = changes_since

                final_sql = cursor.mogrify(sql_template, query_params)

                response = HttpResponse(content=final_sql)
                response['Content-Type'] = 'text/plain'
                return response