# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging
import time

from skipper.core.celery import task  # type: ignore
from typing import List

from rest_framework_simplejwt.utils import aware_utcnow  # type: ignore
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken  # type: ignore

logger = logging.getLogger(__name__)


@task(name='_common_cleanup_outstanding_tokens', queue='celery', ignore_result=True)  # type: ignore
def cleanup_outstanding_tokens() -> None:
    OutstandingToken.objects.filter(expires_at__lte=aware_utcnow()).delete()