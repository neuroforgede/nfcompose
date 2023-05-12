# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.db import transaction, connections
from rest_framework.exceptions import APIException

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.validate import validate_string, validate_sql_string

def escaped_tenant_schema(tenant_name: str) -> str:
    return escape.escape(tenant_schema_unescaped(tenant_name))


def tenant_schema_unescaped(tenant_name: str) -> str:
    if not validate_string(tenant_name):
        raise APIException('Tenant name may only contain letters, numbers and "_".')

    schema_name = f'_3_tenant_{tenant_name}'
    if len(schema_name) > 50:
        raise APIException(f'schema_name {schema_name} was longer than 50 chars')
    return schema_name


def ensure_schema(schema_name: str, connection_name: str) -> None:

    if not validate_sql_string(schema_name):
        raise APIException('Schema name name may only contain letters, numbers, ", "-" and "_".')

    with transaction.atomic():
        # no linting here, creating a new schema does not work with escaped chars for some reason
        with connections[connection_name].cursor() as cursor:
            cursor.execute(
                f"""
                CREATE SCHEMA IF NOT EXISTS {schema_name};
                CREATE SEQUENCE IF NOT EXISTS {schema_name}."_3_dp_sub_clock_seq";
                """
            )
