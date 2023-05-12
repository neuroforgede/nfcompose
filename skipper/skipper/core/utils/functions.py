# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import itertools

from typing import TypeVar, Iterable, Callable, Any, Generator, List

__T = TypeVar('__T')
__U = TypeVar('__U')


def identity(x: __T) -> __T:
    return x

def chunks(iterable: Iterable[__T], size: int = 10, map_fn: Callable[[__T], Any] = lambda x: x) \
        -> Generator[Generator[List[__U], None, None], None, None]:
    iterator = iter(iterable)
    for first in iterator:  # stops when iterator is depleted
        def chunk() -> Generator[List[__U], None, None]:  # construct generator for next chunk
            yield map_fn(first)  # yield element from for loop
            for more in itertools.islice(iterator, size - 1):
                yield map_fn(more)  # yield more elements from the iterator

        yield chunk()  # in outer generator, yield next chunk