# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest
from typing import Optional, Union

from skipper import settings
from skipper.core.models.tenant import Tenant
from urllib import parse

outside_base_path = '/api/flow/impl'

DEFAULT_BASE_PATH = '/api/flow/impl'


def _flow_base_path(tenant: Tenant, user: Optional[Union[User, AnonymousUser]], request: HttpRequest) -> str:
    return DEFAULT_BASE_PATH


def path_from_uri(uri: str) -> str:
    return parse.urlparse(uri).path


try:
    flow_base_path = settings.flow_base_path  # type: ignore
except:
    flow_base_path = _flow_base_path


