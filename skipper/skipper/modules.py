# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from enum import Enum

from skipper import settings


class Module(Enum):
    """
    never change these values, only append
    """
    COMMON = 0
    IMAGE_CUTOUT_TO_LABEL = 1
    APP = 2
    DATA_SERIES = 3
    FLOW = 4
    HEALTH = 5
    TASK = 6
    DEBUG = 7
    CORE = 8


def url_representation(enum: Module) -> str:
    if enum == Module.COMMON:
        return settings.COMMON_MODULE_URL_REPRESENTATION
    elif enum == Module.IMAGE_CUTOUT_TO_LABEL:
        return "image-cutout-to-label"
    elif enum == Module.APP:
        return "app"
    elif enum == Module.DATA_SERIES:
        return "dataseries"
    elif enum == Module.FLOW:
        return "flow"
    elif enum == Module.HEALTH:
        return "health"
    elif enum == Module.TASK:
        return "task"
    elif enum == Module.DEBUG:
        return "debug"
    elif enum == Module.CORE:
        return "core"
    else:
        raise AssertionError(f'unsupported module {enum}')
