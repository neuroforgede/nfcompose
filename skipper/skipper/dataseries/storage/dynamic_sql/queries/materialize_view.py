# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from celery.utils.log import get_task_logger  # type: ignore
from django.db import transaction
from django_multitenant.utils import get_current_tenant, set_current_tenant  # type: ignore
from typing import Dict, Any

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import escape, tenant as tenant_raw_sql
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail, \
    grant_permissions_for_global_analytics_users
from skipper.dataseries.storage.static_ds_information import compute_data_series_query_info
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor

logger = get_task_logger(__name__)


def materialize_view_as(schema_name: str, overwrite: bool, data_series_id: str, view_name: str, refresh_if_exists: bool, cascade_if_delete: bool) -> None:
    """
    :param schema_name:
    :param data_series_id:
    :param view_name: the view name to create
            (will be escaped, so do not manually escape it when passing it to this function
    :return:
    """
    with transaction.atomic():
        data_series = DataSeries.objects.get(id=data_series_id)
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            escaped_view_name = escape.escape(view_name)
            check_for_existence_query = f"""
            SELECT count(*)
            FROM pg_matviews
            WHERE pg_matviews.matviewname=%(view_name)s
            AND pg_matviews.schemaname=%(schema_name)s
            """
            cursor.execute(check_for_existence_query, {
                'view_name': view_name,
                'schema_name': tenant_raw_sql.tenant_schema_unescaped(get_current_tenant().name)
            })
            _row = cursor.fetchone()
            exists_already = _row[0] == 1
            if overwrite:
                cursor.execute(
                    f"""
                    DROP MATERIALIZED VIEW IF EXISTS {schema_name}.{escaped_view_name} {'CASCADE' if cascade_if_delete else ''};
                    """
                )
            if not exists_already:
                query = f"""CREATE MATERIALIZED VIEW IF NOT EXISTS {schema_name}.{escaped_view_name}
                    AS {data_series_as_sql_table(data_series)}"""
                query_params: Dict[str, Any] = {select_info.payload_variable_name: select_info.unescaped_display_id for
                                                select_info in select_infos(compute_data_series_query_info(data_series))}
                cursor.execute(
                    query,
                    query_params
                )
            elif refresh_if_exists:
                cursor.execute(
                    f"""
                    REFRESH MATERIALIZED VIEW {schema_name}.{escaped_view_name};
                    """
                )


def materialize_view(tenant_id: str, schema_name: str, overwrite: bool, data_series_id: str, view_name: str,
                     refresh_if_exists: bool, cascade_if_delete: bool) -> Dict[str, Any]:
    tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))
    view_name = f'matview_{view_name}'
    set_current_tenant(tenant)

    materialize_view_as(schema_name, overwrite, data_series_id, view_name, refresh_if_exists, cascade_if_delete)

    with transaction.atomic():
        grant_permissions_for_global_analytics_users(
            tenant=tenant,
            schema_escaped=schema_name,
            table=view_name
        )
    return {
        "schema_name": tenant_raw_sql.tenant_schema_unescaped(get_current_tenant().name),
        "view_name": view_name
    }
