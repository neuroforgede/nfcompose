# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid

from django.core.files.storage import default_storage
from django.db import connections, transaction
from django_multitenant.utils import set_current_tenant, get_current_tenant  # type: ignore
from typing import Type, List, Union, Dict

from skipper.core.models.tenant import Tenant
from skipper.core.celery import task
from skipper.dataseries.models import data_point_event, truncate_events, ConsumerEventType
from skipper.dataseries.models.metamodel.base_fact import BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.boolean_fact import DataSeries_BooleanFact
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.models.metamodel.float_fact import DataSeries_FloatFact
from skipper.dataseries.models.metamodel.image_fact import DataSeries_ImageFact
from skipper.dataseries.models.metamodel.file_fact import DataSeries_FileFact
from skipper.dataseries.models.metamodel.json_fact import DataSeries_JsonFact
from skipper.dataseries.models.metamodel.string_fact import DataSeries_StringFact
from skipper.dataseries.models.metamodel.text_fact import DataSeries_TextFact
from skipper.dataseries.models.metamodel.timestamp_fact import DataSeries_TimestampFact
from skipper.dataseries.models.partitions import PartitionByUUID
from skipper.dataseries.raw_sql import escape, dbtime
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.contract import StorageBackendType, file_registry
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name, \
    materialized_flat_history_table_name
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


def generate_truncate_query(escaped_table_name: str) -> str:
    return f"""
    TRUNCATE {escaped_table_name};
    """


@task(name="_3_dynamic_sql_truncate_data_series")  # type: ignore
def truncate_data_series(tenant_id: str, data_series_id: str) -> None:
    tenant_obj: Tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))

    set_current_tenant(tenant_obj)

    _data_series_obj: DataSeries = get_or_fail(DataSeries.all_objects.filter(id=data_series_id))

    tables_to_truncate: List[str] = []

    def add_tables_to_truncate(base_table: str, partition_key: Union[str, uuid.UUID]) -> None:
        for elem in PartitionByUUID.objects.filter(
                base_table=base_table,
                partition_key=partition_key
        ).values('child_table_schema', 'child_table'):
            partition_schema_name = elem['child_table_schema']
            schema_prefix = f'{escape.escape(partition_schema_name)}.' if partition_schema_name is not None else ''
            tables_to_truncate.append(f'{schema_prefix}{escape.escape(elem["child_table"])}')

    add_tables_to_truncate('_3_data_point', data_series_id)

    def handle_dims() -> None:
        if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value \
                or _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            # no need to truncate here, all is in one table anyways
            return
        dimension_ids = [elem['dimension_id'] for elem in
                         DataSeries_Dimension.all_objects.filter(data_series_id=data_series_id).values('dimension_id')]  # type: ignore
        for dimension_id in dimension_ids:
            add_tables_to_truncate('_3_data_point_dimension', dimension_id)

    handle_dims()

    def handle_facts(
            type: Type[BaseDataSeriesFactRelation],
            table_name: str
    ) -> None:
        fact_ids = [elem['fact_id'] for elem in
                    type.all_objects.filter(data_series_id=data_series_id).values('fact_id')]  # type: ignore
        for fact_id in fact_ids:
            if (_data_series_obj.backend != StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value
                    and _data_series_obj.backend != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value):
                # the no history backend does not have any partitions to truncate, but file storage fact
                # types need to be truncated in file storage though
                add_tables_to_truncate(table_name, fact_id)

    handle_facts(
        type=DataSeries_BooleanFact,
        table_name='_3_data_point_boolean_fact'
    )
    handle_facts(
        type=DataSeries_FloatFact,
        table_name='_3_data_point_float_fact'
    )
    handle_facts(
        type=DataSeries_ImageFact,
        table_name='_3_data_point_image_fact'
    )
    handle_facts(
        type=DataSeries_JsonFact,
        table_name='_3_data_point_json_fact'
    )
    handle_facts(
        type=DataSeries_StringFact,
        table_name='_3_data_point_string_fact'
    )
    handle_facts(
        type=DataSeries_TextFact,
        table_name='_3_data_point_text_fact'
    )
    handle_facts(
        type=DataSeries_TimestampFact,
        table_name='_3_data_point_timestamp_fact'
    )
    handle_facts(
        type=DataSeries_FileFact,
        table_name='_3_data_point_file_fact'
    )

    if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value or \
        _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        schema_name = escaped_tenant_schema(tenant_obj.name)
        mat_table_name = materialized_table_name(data_series_id, _data_series_obj.external_id)
        tables_to_truncate.append(f'{schema_name}.{escape.escape(mat_table_name)}')

    if _data_series_obj.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        schema_name = escaped_tenant_schema(tenant_obj.name)
        mat_flat_hist_table_name = materialized_flat_history_table_name(data_series_id, _data_series_obj.external_id)
        tables_to_truncate.append(f'{schema_name}.{escape.escape(mat_flat_hist_table_name)}')

    truncate_queries = [generate_truncate_query(table) for table in tables_to_truncate]

    with transaction.atomic():
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            for actual_truncate_query in truncate_queries:
                cursor.execute(
                    actual_truncate_query
                )

            truncate_events(
                tenant=get_current_tenant(),
                data_series_id=data_series_id,
            )

            file_registry.truncate_data_series_data(
                tenant_id=tenant_id,
                data_series_id=data_series_id
            )

            data_point_event(
                tenant=get_current_tenant(),
                point_in_time=dbtime.now(),
                data_series_id=data_series_id,
                payload={
                    'data_series': {
                        'id': data_series_id,
                        'external_id': _data_series_obj.external_id
                    }
                },
                event_type=ConsumerEventType.DATA_SERIES_TRUNCATED,
                sub_clock=dbtime.dp_sub_clock(_data_series_obj.tenant)
            )
