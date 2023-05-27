# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import uuid

from rest_framework.exceptions import APIException
from typing import List, Union, Dict, Any

import skipper.dataseries.storage.dynamic_sql.tasks.ddl.data_series as ddl_data_series
import skipper.dataseries.storage.dynamic_sql.tasks.ddl.dimension as ddl_dimension
import skipper.dataseries.storage.dynamic_sql.tasks.ddl.fact as ddl_fact
import skipper.dataseries.storage.dynamic_sql.tasks.ddl.user_defined_index as ddl_user_defined_index
from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema
from skipper.dataseries.storage.dynamic_sql.tasks import migrate, prune, truncate
from skipper.dataseries.storage.dynamic_sql.queries import create_view as _create_view
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.dataseries.models.metamodel.data_series import DataSeries

# stub: conditional switches go here in the future
handle_create_data_series = ddl_data_series.handle_create_data_series
handle_create_fact = ddl_fact.handle_create_fact
handle_create_dimension = ddl_dimension.handle_create_dimension
handle_create_user_defined_index = ddl_user_defined_index.handle_create_user_defined_index


def nuke_data_series(
        tenant_id: str,
        data_series_id: str,
        older_than: str
) -> None:
    prune.nuke_data_series.delay(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        older_than=older_than
    )


def migrate_no_history_to_flat_history(
    data_series: DataSeries
) -> None:
    # spawn migration task on locked data_series
    migrate.spawn_migrate_no_history_to_flat_history(
        data_series=data_series
    )

def migrate_flat_history_to_no_history(
    data_series: DataSeries
) -> None:
    # spawn migration task on locked data_series
    migrate.spawn_migrate_flat_history_to_no_history(
        data_series=data_series
    )


def prune_history(
    tenant_id: str,
    data_series_id: str,
    older_than: str
) -> None:
    # spawn prune history task
    prune.prune_history.delay(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        older_than=older_than
    )


def prune_metamodel(
    tenant_id: str,
    data_series_id: str,
    older_than: str
) -> None:
    # FIXME: this should really be outside of the dynamic_sql backend
    # spawn prune metamodel task
    prune.prune_meta_model.delay(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        older_than=older_than
    )


def truncate_data_series(
    tenant_id: str, data_series_id: str
) -> None:
    # spawn prune history task
    truncate.truncate_data_series.delay(
        tenant_id=tenant_id,
        data_series_id=data_series_id
    )


def create_view(
        tenant: Tenant,
        data_series_id: Union[uuid.UUID, str],
        overwrite: bool,
        view_name: str,
        materialized: bool,
        cascade_if_delete: bool,
        identify_dimensions_by_external_id: bool,
        full_history: bool
) -> Dict[str, Any]:
    schema_name = escaped_tenant_schema(tenant.name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    if materialized:
        raise APIException()
    else:
        return _create_view.create_view(
            tenant_id=str(tenant.id),
            schema_name=schema_name,
            overwrite=overwrite,
            data_series_id=str(data_series_id),
            view_name=view_name,
            cascade_if_delete=cascade_if_delete,
            identify_dimensions_by_external_id=identify_dimensions_by_external_id,
            full_history=full_history
        )
