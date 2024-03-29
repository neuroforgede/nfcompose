# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.db import connections
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework.exceptions import PermissionDenied
from typing import Any, Dict, List, cast

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql.tenant import tenant_schema_unescaped
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB


def get_views_in_schema(connection: Any, schema: str) -> List[str]:
    with connection.cursor() as cursor:
        views_sql = f"""
        SELECT table_name FROM INFORMATION_SCHEMA.views
        WHERE table_catalog = (SELECT current_database())
        AND table_schema = %s
        ORDER BY table_name ASC
        """
        cursor.execute(
            views_sql,
            [schema]
        )
        return cast(List[str], [elem[0] for elem in cursor.fetchall()])


def get_tables_in_schema(connection: Any, schema: str) -> List[str]:
    with connection.cursor() as cursor:
        tables_sql = f"""
        SELECT table_name FROM INFORMATION_SCHEMA.tables
        WHERE table_catalog = (SELECT current_database())
        AND table_schema = %s
        ORDER BY table_name ASC
        """
        cursor.execute(
            tables_sql,
            [schema]
        )
        return cast(List[str], [elem[0] for elem in cursor.fetchall()])


def get_materialized_views_in_schema(connection: Any, schema: str) -> List[str]:
    with connection.cursor() as cursor:
        views_sql = f"""
        SELECT matviewname
        FROM pg_matviews
        WHERE schemaname = %s
        ORDER BY matviewname ASC
        """
        cursor.execute(
            views_sql,
            [schema]
        )
        return cast(List[str], [elem[0] for elem in cursor.fetchall()])


def get_backend_info() -> Dict[str, Any]:
    tenant: Tenant = get_current_tenant()

    if tenant is None:
        raise PermissionDenied(detail='no tenant set')

    connection = connections[DATA_SERIES_DYNAMIC_SQL_DB]

    schema_name = tenant_schema_unescaped(tenant.name)

    data = {
        'backend_type': 'DYNAMIC_SQL',
        'schema_name': tenant_schema_unescaped(tenant.name),
        'views': get_views_in_schema(connection=connection, schema=schema_name),
        'materialized_views': get_materialized_views_in_schema(connection=connection, schema=schema_name),
        'tables': get_tables_in_schema(connection=connection, schema=schema_name),
    }

    return data
