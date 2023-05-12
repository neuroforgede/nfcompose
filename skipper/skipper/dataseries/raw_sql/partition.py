# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid

from django.db import transaction, connections
from rest_framework.exceptions import APIException
from typing import List, Union

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.partitions import PartitionByUUID
from skipper.dataseries.raw_sql import escape, limit
from skipper.dataseries.raw_sql.tenant import ensure_schema, tenant_schema_unescaped

from skipper.core.lint import sql_cursor


def partition_name(
        base_name: str,
        fact_or_dim_id: str,
        tenant_name: str,
        external_id: str
) -> str:
    return limit.limit_length(f'{base_name}_{str(fact_or_dim_id)}_{tenant_name}_{str(external_id)}')


def partition(
        table_name: str,
        partition_name: str,
        partition_key: Union[str, uuid.UUID],
        connection_name: str,
        tenant: Tenant
) -> None:
    if len(partition_name) > 63:
        raise APIException('partition table names may only be 63 chars long')
    with transaction.atomic():
        with sql_cursor(connection_name) as cursor:
            cursor.execute("set citus.multi_shard_modify_mode to 'sequential'")

            partition_schema = tenant_schema_unescaped(tenant.name)
            if partition_schema is not None:
                ensure_schema(partition_schema, connection_name=connection_name)

            schema_prefix = f'{escape.escape(partition_schema)}.' if partition_schema is not None else ''

            query = f"""CREATE TABLE IF NOT EXISTS {schema_prefix}{escape.escape(partition_name)}
                        PARTITION OF {escape.escape(table_name)}
                        FOR VALUES IN (%s)"""
            cursor.execute(
                query,
                [str(partition_key)]
            )
            to_save = PartitionByUUID.objects.create(
                base_table=table_name,
                child_table=partition_name,
                partition_key=partition_key,
                child_table_schema=partition_schema
            )
            to_save.save()

            cursor.execute("set citus.multi_shard_modify_mode to 'parallel'")


def drop_partition_by_partition_value(
    table_name: str,
    partition_key: Union[str, uuid.UUID],
    connection_name: str
) -> None:
    with transaction.atomic():
        with sql_cursor(connection_name) as cursor:
            cursor.execute("set citus.multi_shard_modify_mode to 'sequential'")

            existing_partition = list(PartitionByUUID.objects.filter(
                base_table=table_name,
                partition_key=partition_key
            ))
            if len(existing_partition) == 1:
                schema_name = existing_partition[0].child_table_schema
                schema_prefix = f'{escape.escape(schema_name)}.' if schema_name is not None else ''
                query = f'DROP TABLE IF EXISTS {schema_prefix}{escape.escape(existing_partition[0].child_table)}'
                cursor.execute(
                    query
                )
                PartitionByUUID.objects.filter(
                    base_table=table_name,
                    child_table=partition_name
                ).delete()

            cursor.execute("set citus.multi_shard_modify_mode to 'parallel'")