# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import re
from typing import TypeVar, Dict

_A = TypeVar('_A')
_B = TypeVar('_B')


def get_or_default(dic: Dict[_A, _B], elem: _A, default: _B) -> _B:
    if elem in dic:
        return dic[elem]
    return default


def underscore(word: str) -> str:
    """
    taken from inflection lib:

    https://inflection.readthedocs.io/en/latest/_modules/inflection.html#underscore
    
    Make an underscored, lowercase form from the expression in the string.

    Example::

        >>> underscore("DeviceType")
        "device_type"

    As a rule of thumb you can think of :func:`underscore` as the inverse of
    :func:`camelize`, though there are cases where that does not hold::

        >>> camelize(underscore("IOError"))
        "IoError"

    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
    word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
    word = word.replace("-", "_")
    return word.lower()
