# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.db import transaction, connections
from rest_framework.exceptions import APIException

from skipper import settings
from skipper.core.models.lock import Lock, POSTGRES_PERMISSIONS_LOCK
from skipper.dataseries.raw_sql import escape
from skipper.core.lint import sql_cursor


# noinspection DuplicatedCode
def grant_select_permissions(role: str, schema_escaped: str, table: str, connection_name: str) -> None:
    if len(role) > 63:
        raise APIException('role names may only be 63 chars long')
    if role in settings.SYSTEM_POSTGRES_DATABASE_ROLES:
        raise APIException(f'system database roles like {role} can not be managed')
    with transaction.atomic():
        Lock.objects.aquire_lock(key=POSTGRES_PERMISSIONS_LOCK)
        with sql_cursor(connection_name) as cursor:
            query = f"""
                    GRANT USAGE ON SCHEMA {schema_escaped} TO {escape.escape(role)};
                    GRANT SELECT ON TABLE {schema_escaped}.{escape.escape(table)} TO {escape.escape(role)};
                    """
            cursor.execute(
                query
            )


# noinspection DuplicatedCode
def revoke_select_permissions(role: str, schema_escaped: str, table: str, connection_name: str) -> None:
    if len(role) > 63:
        raise APIException('role names may only be 63 chars long')
    if role in settings.SYSTEM_POSTGRES_DATABASE_ROLES:
        raise APIException(f'system database roles like {role} can not be managed')
    with transaction.atomic():
        Lock.objects.aquire_lock(key=POSTGRES_PERMISSIONS_LOCK)
        with sql_cursor(connection_name) as cursor:

            query = f"""
                    REVOKE USAGE ON SCHEMA {schema_escaped} FROM {escape.escape(role)};
                    REVOKE SELECT ON TABLE {schema_escaped}.{escape.escape(table)} FROM {escape.escape(role)}
                    """
            cursor.execute(
                query
            )
