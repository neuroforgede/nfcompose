# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import List, Any


def list_empty(x: List[Any]) -> bool:
    for elem in x:
        if not elem.empty():
            return False
    return True


class EmptyMixin(object):
    def empty(self) -> bool:
        for key, value in self.__dict__.items():
            if key != 'external_id':
                if isinstance(value, list):
                    if not list_empty(value):
                        return False
                elif value is not None and not value.empty():
                    return False
        return True