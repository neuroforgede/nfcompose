# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db.models import Model
from typing import List


class DebugPermissions(Model):
    """
    global debug permissions, not really a model
    that stores any real data
    """
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            ('telemetry.ui', 'Allowed to view the debug telemetry ui'),
        )
