# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.db import transaction
from django_multitenant.utils import set_current_tenant  # type: ignore
from typing import List, Tuple, Dict, Callable

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.contract import FactType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name, materialized_table_name
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.data_series import handle_create_data_series_materialized
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.fact import handle_create_fact_materialized
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.dimension import handle_create_dimension_materialized
from skipper.dataseries.storage.static_ds_information import data_point_serialization_keys, DataSeriesQueryInfo, \
    compute_data_series_query_info
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor
from skipper.dataseries.models.task_data import MetaModelTaskData


def register(registry: Dict[str, Callable[[MetaModelTaskData], None]]) -> None:
    registry['_3_dynamic_sql_migrate_v1_to_materialized'] = _run_migrate_v1_to_materialized


def spawn_migrate_v1_to_materialized(
    data_series: DataSeries
) -> None:
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import spawn
    spawn.spawn_migrate_task(
        data_series=data_series,
        task_name='_3_dynamic_sql_migrate_v1_to_materialized'
    )


def _run_migrate_v1_to_materialized(
    meta_model_task_data: MetaModelTaskData
) -> None:
    _data_series: DataSeries = meta_model_task_data.data_series
    _migrate_v1_to_materialized(
        data_series_id = str(_data_series.id),
        data_series_external_id = _data_series.external_id,
        tenant_id=str(_data_series.tenant.id),
        tenant_name=_data_series.tenant.name
    )


def _migrate_v1_to_materialized(
        data_series_id: str,
        data_series_external_id: str,
        tenant_id: str,
        tenant_name: str
) -> None:
    tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))
    set_current_tenant(tenant)

    with transaction.atomic():
        # create database structure
        data_series: DataSeries = DataSeries.objects.select_for_update().get(id=data_series_id)

        data_series_query_info = compute_data_series_query_info(data_series)
        _data_point_serialization_keys = data_point_serialization_keys(data_series_query_info)

        # simulate creation
        handle_create_data_series_materialized(data_series_id, data_series_external_id, tenant_name, tenant=tenant)

        def handle_facts(fact_relations: List[Tuple[str, str]], fact_type: FactType) -> None:
            for external_id, uuid in fact_relations:
                handle_create_fact_materialized(
                    data_series_id=data_series_id,
                    data_series_external_id=data_series_external_id,
                    fact_id=uuid,
                    fact_type=fact_type,
                    tenant_name=tenant_name,
                    external_id=external_id
                )

        handle_facts(_data_point_serialization_keys['float_facts'], FactType.Float)
        handle_facts(_data_point_serialization_keys['boolean_facts'], FactType.Boolean)
        handle_facts(_data_point_serialization_keys['image_facts'], FactType.Image)
        handle_facts(_data_point_serialization_keys['file_facts'], FactType.File)
        handle_facts(_data_point_serialization_keys['json_facts'], FactType.JSON)
        handle_facts(_data_point_serialization_keys['string_facts'], FactType.String)
        handle_facts(_data_point_serialization_keys['text_facts'], FactType.Text)
        handle_facts(_data_point_serialization_keys['timestamp_facts'], FactType.Timestamp)

        def handle_dimensions(dim_relations: List[Tuple[str, str]]) -> None:
            for external_id, uuid in dim_relations:
                handle_create_dimension_materialized(
                    data_series_id=data_series_id,
                    data_series_external_id=data_series_external_id,
                    dimension_id=uuid,
                    tenant_name=tenant_name,
                    external_id=external_id
                )

        handle_dimensions(_data_point_serialization_keys['dimensions'])

    with transaction.atomic():
        # now migrate all the data
        _materialize_data(
            data_series=data_series,
            data_series_id=data_series_id,
            data_series_external_id=data_series_external_id,
            data_series_query_info=data_series_query_info,
            tenant_name=tenant_name
        )

        data_series.locked = False
        data_series.save()


def _materialize_data(
        data_series: DataSeries,
        data_series_id: str,
        data_series_external_id: str,
        data_series_query_info: DataSeriesQueryInfo,
        tenant_name: str
) -> None:
    from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
    data_query = data_series_as_sql_table(data_series, use_materialized=False)

    all_select_infos = select_infos(data_series_query_info)
    _data_point_serialization_keys = data_point_serialization_keys(data_series_query_info)

    schema_name = escaped_tenant_schema(tenant_name)
    table_name = escape.escape(materialized_table_name(data_series_id, data_series_external_id))

    columns = ['id', 'external_id', 'point_in_time', 'inserted_at', 'deleted_at']
    data_query_columns = ['id', 'external_id', 'point_in_time', 'point_in_time', 'NULL', ]
    set_statements = ['deleted_at = EXCLUDED.deleted_at']

    for select_info in all_select_infos:
        column = escape.escape(materialized_column_name(select_info.actual_id, select_info.unescaped_display_id))
        data_query_column = select_info.select_alias
        set_statement = f'{column} = EXCLUDED.{column}'

        columns.append(column)
        data_query_columns.append(data_query_column)
        set_statements.append(set_statement)

    # inserted_at is not the date the point was created the first time, but instead the first date
    # the datapoint was materialized. This is by design. For datapoints that were deleted and then inserted again,
    # what would be the correct way of handling the migration, the initial date, the last date it was created?

    # this does not include deleted entries -> we can always add a recreate from history feature if we want to
    materialize_query = f"""
    INSERT INTO {schema_name}.{table_name}(
         {','.join(columns)}
    )
    SELECT {','.join(data_query_columns)}
    FROM (
        {data_query}
    ) current
    ON CONFLICT (id) DO UPDATE SET {','.join(set_statements)};
    """

    with transaction.atomic():
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(materialize_query)
