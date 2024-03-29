# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.db import migrations

class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0015_ensure_indexes_materialized'),
        ('dataseries', '0044_partitionbyuuid_child_table_schema')
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0017_move_existing_partitions_to_tenant_schema')
    ]

    operations = [] # type: ignore
