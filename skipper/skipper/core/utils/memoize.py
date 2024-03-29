# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import TypeVar, Generic, Callable, Dict

_MemoizedValue = TypeVar('_MemoizedValue', covariant=True)
_MemoizeKey = TypeVar('_MemoizeKey')


class Memoize(Generic[_MemoizeKey, _MemoizedValue]):
    """
    Memoize any function
    """

    def __init__(self, f: Callable[[_MemoizeKey], _MemoizedValue]):
        self.f = f
        self.memo: Dict[_MemoizeKey, _MemoizedValue] = {}

    def __call__(self, key: _MemoizeKey) -> _MemoizedValue:
        if not key in self.memo:
            self.memo[key] = self.f(key)
        return self.memo[key]