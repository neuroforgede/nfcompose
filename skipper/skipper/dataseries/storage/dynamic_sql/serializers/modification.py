# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
from django.db import transaction
from django.utils import timezone
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework.exceptions import NotFound
from typing import Dict, Any, Optional

from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract.base import BaseDataPointModificationSerializer
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint, DisplayDataPoint
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.dynamic_sql.serializers.display import \
    display_data_point_serializer_class
from skipper.dataseries.storage.dynamic_sql.tasks.persist_data_point import create_data_points, \
    set_missing_structure_elements_to_none
from skipper.dataseries.storage.static_ds_information import DataPointSerializationKeys


class DataPointModificationSerializer(BaseDataPointModificationSerializer):

    serialization_keys: DataPointSerializationKeys

    def impl_internal_to_representation(
            self,
            data_point: Any,
            data_series: DataSeries,
            external_id_as_dimension_identifier: bool
    ) -> Dict[str, Any]:
        display_serializer = display_data_point_serializer_class(
            self.should_include_versions,
            self.data_series_children_query_info
        )(context=self.context)
        query_params: Dict[str, Any] = {select_info.payload_variable_name: select_info.unescaped_display_id for
                                        select_info in
                                        select_infos(self.get_data_series_children_query_info())}

        query_str = data_series_as_sql_table(
            data_series=data_series,
            include_in_payload=None,
            payload_as_json=True,
            point_in_time=self.point_in_time is not None,
            include_versions=self.should_include_versions,
            filter_str='AND ds_dp.id = %(data_point_id)s',
            resolve_dimension_external_ids=external_id_as_dimension_identifier,
            data_series_query_info=self.data_series_children_query_info
        )

        query_params['data_point_id'] = data_point.id
        if self.point_in_time is not None:
            query_params['point_in_time'] = self.point_in_time

        display_data_points = DisplayDataPoint.objects.raw(query_str, query_params)

        if len(display_data_points) != 1:
            raise NotFound(f'no data point found for id {data_point.id}')

        return display_serializer.to_representation(
            display_data_points[0]
        )

    def impl_create(
            self,
            validated_data: Dict[str, Any],
            user_id: str,
            record_source: str,
            data_series_id: str,
            data_series_external_id: str,
            data_series_backend: str,
            timestamp: datetime.datetime,
            sub_clock: int
    ) -> Any:
        with transaction.atomic():
            return create_data_points(
                get_current_tenant().id,
                get_current_tenant().name,
                data_series_id,
                data_series_external_id,
                data_series_backend,
                [validated_data],
                self.serialization_keys,
                timestamp,
                user_id=user_id,
                record_source=record_source,
                partial=False,
                sub_clock=sub_clock
            )[0]

    def impl_update(
            self,
            data_point: DataPoint,
            validated_data: Dict[str, Any],
            user_id: str,
            record_source: str,
            data_series_id: str,
            data_series_external_id: str,
            data_series_backend: str,
            timestamp: datetime.datetime,
            sub_clock: int
    ) -> Any:

        if not self.patch:
            # if we do a regular update
            # and a key is left out, this is considered a
            # delete action
            set_missing_structure_elements_to_none(self.serialization_keys, validated_data)

        with transaction.atomic():
            new_data_point = create_data_points(
                get_current_tenant().id,
                get_current_tenant().name,
                data_series_id,
                data_series_external_id,
                data_series_backend,
                [validated_data],
                self.serialization_keys,
                dbtime.now(),
                user_id=user_id,
                record_source=record_source,
                partial=self.patch,
                sub_clock=sub_clock
            )[0]
        return new_data_point

    class Meta:
        model = DataPoint
        fields = ['url', 'history_url', 'id', 'identify_dimensions_by_external_id', 'external_id', 'payload']
