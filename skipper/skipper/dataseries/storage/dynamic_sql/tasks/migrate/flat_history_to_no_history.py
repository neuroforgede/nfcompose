# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import datetime
from django.db import transaction
from django_multitenant.utils import set_current_tenant  # type: ignore
from typing import Dict, Callable

from skipper.core.celery import task
from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail
from skipper.dataseries.storage.dynamic_sql.tasks.prune import prune_history
from skipper.dataseries.storage.static_ds_information import data_point_serialization_keys, \
    compute_data_series_query_info
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.user_defined_index import handle_drop_user_defined_index_by_target_table_type
from skipper.core.lint import sql_cursor
from skipper.dataseries.models.metamodel.index import TargetTableType
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_flat_history_table_name
from skipper.dataseries.models.task_data import MetaModelTaskData

def register(registry: Dict[str, Callable[[MetaModelTaskData], None]]) -> None:
    registry['_3_dynamic_sql_migrate_flat_history_to_no_history'] = _run_migrate_flat_history_to_no_history


def spawn_migrate_flat_history_to_no_history(
    data_series: DataSeries
) -> None:
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import spawn
    spawn.spawn_migrate_task(
        data_series=data_series,
        task_name='_3_dynamic_sql_migrate_flat_history_to_no_history'
    )


def _run_migrate_flat_history_to_no_history(
    meta_model_task_data: MetaModelTaskData
) -> None:
    _data_series: DataSeries = meta_model_task_data.data_series
    _migrate_flat_history_to_no_history(
        data_series_id = str(_data_series.id),
        tenant_id=str(_data_series.tenant.id)
    )


def _migrate_flat_history_to_no_history(
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
        
        prune_history(tenant_id=str(tenant.id), data_series_id=data_series_id,
                      older_than=datetime.datetime(
                          year=4000,
                          month=1,
                          day=1,
                          hour=1,
                          minute=1,
                          second=1,
                          microsecond=1
                      ).isoformat())


    for index in data_series.dataseries_userdefinedindex_set.all():
        handle_drop_user_defined_index_by_target_table_type(
            index_id=index.user_defined_index.id,
            target_table_type=TargetTableType.FLAT_HISTORY,
            escaped_schema_name=escaped_tenant_schema(tenant.name)
        )

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        schema_name = escaped_tenant_schema(tenant.name)
        table_name = escape.escape(materialized_flat_history_table_name(data_series_id, data_series.external_id))
        cursor.execute(f'DROP TABLE IF EXISTS {schema_name}.{table_name}')

    with transaction.atomic():
        data_series.locked = False
        data_series.save()
