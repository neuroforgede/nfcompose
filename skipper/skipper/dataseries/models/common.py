# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Any

from django.core.exceptions import ValidationError

from skipper.core.utils import snippet
from skipper.modules import Module


def validate_json_not_null(json: Any) -> None:
    if json is None:
        raise ValidationError('This field may not be null')


def calc_db_table(name: str) -> str:
    return '_' + str(Module.DATA_SERIES.value) + "_" + snippet.underscore(name)


