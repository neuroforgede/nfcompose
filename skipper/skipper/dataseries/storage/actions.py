# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


"""
This Module routes all actions that are not directly handled by the StorageViewAdapter itself
to the correct storage backend
"""
import uuid

from rest_framework.exceptions import APIException
from typing import List, Union, Dict, Any

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.contract import FactType, StorageBackendType


def handle_migrate_data_series_backend(
        data_series: DataSeries,
        tenant_id: str,
        tenant_name: str,
        old_backend: str,
        new_backend: str
) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    if old_backend == StorageBackendType.DYNAMIC_SQL_V1.value and new_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value:
        dynamic_sql_actions.migrate_v1_to_materialized(
            data_series=data_series
        )
    elif old_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value \
            and new_backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
        dynamic_sql_actions.migrate_materialized_to_no_history(
            data_series=data_series
        )
    elif old_backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value \
            and new_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        dynamic_sql_actions.migrate_no_history_to_flat_history(
            data_series=data_series
        )
    elif old_backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value \
            and new_backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
        dynamic_sql_actions.migrate_flat_history_to_no_history(
            data_series=data_series
        )
    else:
        raise APIException(f'unexpected change from backend {old_backend} to {new_backend}')


def handle_create_data_series(data_series_id: uuid.UUID, data_series_external_id: str, tenant_name: str,
                              external_id: str, backend: str, tenant_id: str) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.handle_create_data_series(data_series_id=data_series_id,
                                                  data_series_external_id=data_series_external_id,
                                                  tenant_name=tenant_name, external_id=external_id, backend=backend,
                                                  tenant_id=tenant_id)


def handle_create_fact(data_series_id: uuid.UUID, data_series_external_id: str, fact_id: str, fact_type: FactType,
                       tenant_name: str, external_id: str, backend: str, tenant_id: str) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.handle_create_fact(data_series_id=data_series_id,
                                           data_series_external_id=data_series_external_id, fact_id=fact_id,
                                           fact_type=fact_type, tenant_name=tenant_name, external_id=external_id,
                                           backend=backend, tenant_id=tenant_id)


def handle_create_dimension(data_series_id: uuid.UUID, data_series_external_id: str, dimension_id: str,
                            tenant_name: str, external_id: str, backend: str, tenant_id: str) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.handle_create_dimension(data_series_id=data_series_id,
                                                data_series_external_id=data_series_external_id,
                                                dimension_id=dimension_id, tenant_name=tenant_name,
                                                external_id=external_id, backend=backend, tenant_id=tenant_id)


def handle_create_user_defined_index(data_series_id: uuid.UUID, data_series_external_id: str, tenant_name: str, tenant_id: str,
                                     targets: List[Dict[str, Union[uuid.UUID, str]]], backend: str, index_id: uuid.UUID) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.handle_create_user_defined_index(data_series_id=data_series_id, 
                                                         data_series_external_id=data_series_external_id,
                                                         tenant_name=tenant_name,
                                                         targets=targets, backend=backend,
                                                         index_id=index_id)


def nuke_data_series(
    tenant_id: str,
    backend_type: str,
    data_series_id: str,
    older_than: str
) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.nuke_data_series(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        older_than=older_than
    )


def prune_history(
    tenant_id: str,
    data_series_id: str,
    older_than: str
) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.prune_history(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        older_than=older_than
    )


def prune_metamodel(
    tenant_id: str,
    data_series_id: str,
    older_than: str
) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    # FIXME: this should really be outside of the dynamic_sql backend
    dynamic_sql_actions.prune_metamodel(
        tenant_id=tenant_id,
        data_series_id=data_series_id,
        older_than=older_than
    )


def truncate_data_series(
    tenant_id: str, data_series_id: str
) -> None:
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    dynamic_sql_actions.truncate_data_series(
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
    from skipper.dataseries.storage.dynamic_sql import actions as dynamic_sql_actions
    return dynamic_sql_actions.create_view(
        tenant=tenant,
        data_series_id=data_series_id,
        overwrite=overwrite,
        view_name=view_name,
        materialized=materialized,
        cascade_if_delete=cascade_if_delete,
        identify_dimensions_by_external_id=identify_dimensions_by_external_id,
        full_history=full_history
    )
