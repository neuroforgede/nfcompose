# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import uuid
from django.db import transaction
from django_multitenant.utils import set_current_tenant  # type: ignore
from psycopg2 import errors  # type: ignore
from typing import List, Tuple, Dict, Union, Callable, Dict

from skipper.core.celery import task
from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.contract import FactType
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.fact import handle_create_fact_materialized_flat_history
from skipper.dataseries.storage.static_ds_information import data_point_serialization_keys, \
    compute_data_series_query_info
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.data_series import handle_create_data_series_materialized_flat_history
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.dimension import handle_create_dimension_materialized_flat_history
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.user_defined_index import handle_create_user_defined_index
from skipper.core.lint import sql_cursor
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.history import insert_to_flat_history_query
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name
from skipper.dataseries.models.task_data import MetaModelTaskData

def register(registry: Dict[str, Callable[[MetaModelTaskData], None]]) -> None:
    registry['_3_dynamic_sql_migrate_no_history_to_flat_history'] = _run_migrate_no_history_to_flat_history


def spawn_migrate_no_history_to_flat_history(
    data_series: DataSeries
) -> None:
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import spawn
    spawn.spawn_migrate_task(
        data_series=data_series,
        task_name='_3_dynamic_sql_migrate_no_history_to_flat_history'
    )


def _run_migrate_no_history_to_flat_history(
    meta_model_task_data: MetaModelTaskData
) -> None:
    _data_series: DataSeries = meta_model_task_data.data_series
    _migrate_no_history_to_flat_history(
        data_series_id = str(_data_series.id),
        tenant_id=str(_data_series.tenant.id)
    )


def _migrate_no_history_to_flat_history(
        data_series_id: str,
        tenant_id: str
) -> None:
    tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))
    set_current_tenant(tenant)

    with transaction.atomic():
        # create database structure
        data_series: DataSeries = DataSeries.objects.select_for_update().get(id=data_series_id)

        data_series_query_info = compute_data_series_query_info(data_series)
        _data_point_serialization_keys = data_point_serialization_keys(data_series_query_info)

        # simulate creation
        handle_create_data_series_materialized_flat_history(
            data_series_id=data_series_id,
            data_series_external_id=data_series.external_id, 
            tenant_name=tenant.name, 
            tenant=tenant
        )

        def handle_facts(fact_relations: List[Tuple[str, str]], fact_type: FactType) -> None:
            for external_id, uuid in fact_relations:
                handle_create_fact_materialized_flat_history(
                    data_series_id=data_series_id,
                    data_series_external_id=data_series.external_id,
                    fact_id=uuid,
                    fact_type=fact_type,
                    tenant_name=tenant.name,
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
                handle_create_dimension_materialized_flat_history(
                    data_series_id=data_series_id,
                    data_series_external_id=data_series.external_id,
                    dimension_id=uuid,
                    tenant_name=tenant.name,
                    external_id=external_id
                )

        handle_dimensions(_data_point_serialization_keys['dimensions'])

        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            schema_name = escaped_tenant_schema(tenant.name)
            non_historical_table_name = escape.escape(materialized_table_name(data_series_id, data_series.external_id))
            insert_sql = insert_to_flat_history_query(
                data_series_id=data_series_id,
                data_series_external_id=data_series.external_id,
                user_id=None,
                record_source='migration - no history to flat history',
                cursor=cursor,
                source_query=f'SELECT * FROM {schema_name}.{non_historical_table_name}',
                escaped_schema_name=schema_name,
                data_point_serialization_keys=data_point_serialization_keys(data_series_query_info)
            )
            cursor.execute(
                insert_sql
            )

        for index in data_series.dataseries_userdefinedindex_set.all():
            targets: List[Dict[str, Union[str, uuid.UUID]]] = []
            for target in index.user_defined_index.userdefinedindex_target_set\
                .order_by('target_position_in_index_order').all():
                targets.append({
                    "target_type": target.target_type,
                    "target_id": target.target_id
                })
            
            # simply re-run the index creation.
            handle_create_user_defined_index(
                data_series_id=data_series_id,
                data_series_external_id=data_series.external_id,
                tenant_name=tenant.name,
                targets=targets,
                backend=data_series.backend,
                index_id=index.user_defined_index.id
            )

    with transaction.atomic():
        data_series.locked = False
        data_series.save()
