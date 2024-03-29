# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
from django.db import transaction, connections
from typing import cast

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor

def now() -> datetime.datetime:
    with transaction.atomic():
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(f'SELECT clock_timestamp()')
            return cast(datetime.datetime, cursor.fetchone()[0])


def dp_sub_clock(tenant: Tenant) -> int:
    with transaction.atomic():
        schema_name = escaped_tenant_schema(tenant.name)
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(f'SELECT nextval(\'{schema_name}."_3_dp_sub_clock_seq"\')')
            return cast(int, cursor.fetchone()[0])
