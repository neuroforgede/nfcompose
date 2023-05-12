# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.core.files.storage import default_storage
from django.db import transaction
from typing import List

from skipper.core.models import default_media_storage
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.testing import SKIPPER_CELERY_TESTING


def data_series_dir(
        tenant_name: str,
        data_series_id: str
) -> str:
    return f'_3_tenant_{tenant_name}/dataseries/{data_series_id}/'


def file_based_fact_dir(
        tenant_name: str,
        data_series_id: str,
        fact_id: str,
        fact_type: str
) -> str:
    return f'{data_series_dir(tenant_name, data_series_id)}{fact_type}_fact/{fact_id}/'
