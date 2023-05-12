# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import re

from django.core import exceptions
from django.core.exceptions import ValidationError
from typing import Any


def validate_json_not_null(json: Any) -> None:
    if json is None:
        raise exceptions.ValidationError('This field may not be null')


def validate_external_id_sql_safe(external_id: str) -> bool:
    regex = re.compile('[a-zA-Z0-9_]{1,50}')
    return regex.fullmatch(external_id) is not None


def external_id_validator_sql_safe(external_id: str) -> None:
    if not validate_external_id_sql_safe(external_id):
        raise ValidationError('%(value)s is not a valid external_id', params={'value': external_id})


def validate_external_id_url_safe(external_id: str) -> bool:
    regex = re.compile('[a-zA-Z0-9_-]{1,256}')
    return regex.fullmatch(external_id) is not None


def external_id_validator_url_safe(external_id: str) -> None:
    if not validate_external_id_url_safe(external_id):
        raise ValidationError('%(value)s is not a valid external_id', params={'value': external_id})
