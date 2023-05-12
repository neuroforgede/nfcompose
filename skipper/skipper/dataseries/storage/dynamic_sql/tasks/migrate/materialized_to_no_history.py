# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import datetime
from django.db import transaction
from django_multitenant.utils import set_current_tenant  # type: ignore
from psycopg2 import errors  # type: ignore
from typing import cast, Any, Dict, Callable, Union

from skipper.core.celery import task
from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.raw_sql import partition
from skipper.dataseries.storage.contract import FactType
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail
from skipper.dataseries.storage.dynamic_sql.tasks.ddl.fact import fact_ddl_names
from skipper.dataseries.storage.dynamic_sql.tasks.prune import prune_history
from skipper.dataseries.storage.static_ds_information import data_point_serialization_keys, \
    compute_data_series_query_info, all_facts
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.dataseries.models.task_data import MetaModelTaskData


def register(registry: Dict[str, Callable[[MetaModelTaskData], None]]) -> None:
    registry['_3_dynamic_sql_migrate_materialized_to_no_history'] = _run_migrate_materialized_to_no_history


def spawn_migrate_materialized_to_no_history(
    data_series: DataSeries
) -> None:
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import spawn
    spawn.spawn_migrate_task(
        data_series=data_series,
        task_name='_3_dynamic_sql_migrate_materialized_to_no_history'
    )


def _run_migrate_materialized_to_no_history(
    meta_model_task_data: MetaModelTaskData
) -> None:
    _data_series: DataSeries = meta_model_task_data.data_series
    _migrate_materialized_to_no_history(
        data_series_id = str(_data_series.id),
        tenant_id=str(_data_series.tenant.id)
    )

def _migrate_materialized_to_no_history(
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

        # prune everything (including s3 data) to get rid of all old data first
        # We do this before dropping the partitions to prune all data properly that is stored outside
        # of the database
        # FIXME: we can do this smarter by only pruning the s3 data and then simply dropping the partitions
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

        # drop all partitions in the historical fact tables
        for fact_rel in list(all_facts(data_series).all()):
            _type: str = cast(Any, fact_rel).type
            _type_enum: FactType = FactType(cast(Any, fact_rel).type_enum)

            dp_rel_table_name, dp_rel_partition_base_name = fact_ddl_names(_type_enum)
            partition.drop_partition_by_partition_value(
                table_name=dp_rel_table_name,
                partition_key=fact_rel.fact.id,
                connection_name=DATA_SERIES_DYNAMIC_SQL_DB
            )

        for dim_rel in list(DataSeries_Dimension.all_objects.filter(
                data_series=data_series
        ).select_related('dimension').all()):
            table_name = '_3_data_point_dimension'
            partition.drop_partition_by_partition_value(
                table_name=table_name,
                partition_key=dim_rel.dimension.id,
                connection_name=DATA_SERIES_DYNAMIC_SQL_DB
            )

        # non user defined indexes still work the same here

    with transaction.atomic():
        data_series.locked = False
        data_series.save()
