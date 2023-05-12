# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import dataclasses

from celery.utils.log import get_task_logger  # type: ignore
from django.db import transaction, InternalError
from django_multitenant.utils import set_current_tenant, get_current_tenant  # type: ignore
from rest_framework.exceptions import ValidationError
from typing import Dict, Any

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import escape, tenant as tenant_raw_sql
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.dynamic_sql.tasks.common import get_or_fail, \
    grant_permissions_for_global_analytics_users
from skipper.dataseries.storage.static_ds_information import compute_data_series_query_info, \
    data_series_query_info_for_full_history
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor

logger = get_task_logger(__name__)


def create_view_as(
        schema_name: str,
        overwrite: bool,
        identify_dimensions_by_external_id: bool,
        data_series_id: str,
        view_name: str,
        cascade_if_delete: bool,
        full_history: bool
) -> None:
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
            FROM INFORMATION_SCHEMA.views
            WHERE table_catalog = (SELECT current_database())
            AND table_schema = %(schema_name)s
            AND table_name = %(view_name)s
            """
            cursor.execute(check_for_existence_query, {
                'view_name': view_name,
                'schema_name': tenant_raw_sql.tenant_schema_unescaped(get_current_tenant().name)
            })
            _row = cursor.fetchone()
            exists_already = _row[0] == 1

            if overwrite:
                try:
                    cursor.execute(
                        f"""
                        DROP VIEW IF EXISTS {schema_name}.{escaped_view_name} {'CASCADE' if cascade_if_delete else ''};
                        """
                    )
                except InternalError as e:
                    raise ValidationError(f'failed to drop view {view_name}, does this view have'
                                          ' another database object depending on it?')
            elif exists_already:
                raise ValidationError(f'a view with name {view_name} already exists')

            data_series_query_info = compute_data_series_query_info(
                data_series
            )

            if full_history:
                data_series_query_info = data_series_query_info_for_full_history(
                    data_series_query_info,
                )

            data_sql = data_series_as_sql_table(
                data_series,
                data_series_query_info=data_series_query_info,
                resolve_dimension_external_ids=identify_dimensions_by_external_id
            )

            query = f"""CREATE VIEW {schema_name}.{escaped_view_name}
                AS {data_sql}"""
            query_params: Dict[str, Any] = {select_info.payload_variable_name: select_info.unescaped_display_id for
                                            select_info in select_infos(compute_data_series_query_info(data_series))}
            cursor.execute(
                query,
                query_params
            )


def create_view(
        tenant_id: str,
        schema_name: str,
        overwrite: bool,
        data_series_id: str,
        view_name: str,
        cascade_if_delete: bool,
        identify_dimensions_by_external_id: bool,
        full_history: bool
) -> Dict[str, Any]:
    tenant = get_or_fail(Tenant.objects.filter(id=tenant_id))
    view_name = f'view_{view_name}'
    set_current_tenant(tenant)

    create_view_as(
        schema_name,
        overwrite,
        identify_dimensions_by_external_id,
        data_series_id,
        view_name,
        cascade_if_delete,
        full_history
    )

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
