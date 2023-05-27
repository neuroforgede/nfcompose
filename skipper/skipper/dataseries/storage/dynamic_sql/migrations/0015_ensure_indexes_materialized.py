# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import migrations
from typing import Any

class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0014_consumer'),
        ('dataseries', '0023_consumerevent'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0015_ensure_indexes_materialized')
    ]

    operations = []  # type: ignore
