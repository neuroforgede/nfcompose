# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import re
from typing import Optional

from django.db.models import QuerySet

from skipper import settings
from skipper.core.models.tenant import Tenant


def get_tenant_from_hostname(host_name: str) -> Optional[Tenant]:
    base_domain = settings.BASE_DOMAIN
    regex_result = re.match(f'([a-zA-Z0-9]+).{base_domain}(:[0-9]+)?', host_name, re.IGNORECASE)
    if regex_result:
        tenant_identifier = regex_result.group(1)
        tenant: 'QuerySet[Tenant]' = Tenant.objects.filter(name=tenant_identifier).all()
        if len(tenant) > 0:
            return tenant[0]
    return None
