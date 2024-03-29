# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Protocol, TypeVar, Any, Dict, List, Tuple, Iterable

from library.client import APIClient

T = TypeVar('T', covariant=True)


class APIConverter(Protocol[T]):
    def __call__(self, json: Dict[str, Any]) -> T: ...


def parse_page(
        page_data: Dict[str, Any],
        converter: APIConverter[T],
        data_key: str
) -> Tuple[Iterable[T], str]:
    if data_key not in page_data:
        raise AssertionError(f'did not find {data_key} in page data')

    converted = map(converter, page_data[data_key])

    return converted, page_data['next']


def read_paginated_all(client: APIClient, url: str, converter: APIConverter[T], data_key: str = 'results') -> Iterable[T]:
    ret: List[T] = []

    _url = url

    while _url is not None:
        page_data = client.get(url=_url)

        parsed_data, _url = parse_page(page_data, converter, data_key)
        ret.extend(parsed_data)

    return ret


def read_paginated_generator(client: APIClient, url: str, converter: APIConverter[T], data_key: str = 'results') -> Iterable[T]:
    ret: List[T] = []

    _url = url

    while _url is not None:
        page_data = client.get(url=_url)

        parsed_data, _url = parse_page(page_data, converter, data_key)
        for elem in parsed_data:
            yield elem

    return ret


def read_list(client: APIClient, url: str, converter: APIConverter[T]) -> Iterable[T]:
    data = client.get(url=url)
    converted = map(converter, data)
    return list(converted)






