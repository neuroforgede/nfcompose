# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Tuple, List, cast

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import StorageBackendType

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


def test_pagination_is_stable(self: 'DataPointPaginationTest', backend_key: str) -> None:
    data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
        'name': f'my_data_series_with_extra_keys_{backend_key}',
        'external_id': f'_external_id_1_{backend_key}',
        'allow_extra_fields': False,
        'backend': backend_key
    }, simulate_tenant=False)

    data = []
    for i in range(0, 10):
        dp = self.create_payload(url=data_series['data_points'], payload=lambda: {
            'external_id': str(i),
        }, format='multipart', equality_check=False)
        self.assertEqual(dp['external_id'], str(i))
        data.append(dp)

    data.sort(key=lambda x: cast(str, x['external_id']))

    page_size = 2

    page = self.get_payload(url=data_series['data_points'] + f'?include_prev&pagesize={str(page_size)}')

    will_be_deleted = page['data'][0]

    # delete the first one
    self.delete_payload(
        url=will_be_deleted['url']
    )
    page['data'].pop(0)

    # recreate it
    self.create_payload(
        url=data_series['data_points'],
        payload=will_be_deleted
    )

    # pagination should not be broken, first one should now be last one
    collected_forwards = []

    next_url = ''
    while next_url is not None:
        cnt = 0
        for elem in page['data']:
            collected_forwards.append(elem['external_id'])
            cnt += 1

        self.assertTrue(cnt <= page_size)

        next_url = page['next']
        if next_url is not None:
            page = self.get_payload(url=next_url)

    page = self.get_payload(url=data_series['data_points'] + f'?include_prev&pagesize={str(page_size)}')
    collected_again = []

    next_url = ''
    while next_url is not None:
        cnt = 0
        for elem in page['data']:
            collected_again.append(elem['external_id'])
            cnt += 1

        self.assertTrue(cnt <= page_size)

        next_url = page['next']
        if next_url is not None:
            page = self.get_payload(url=next_url)

    self.assertEqual(collected_forwards, collected_again)


class DataPointPaginationTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_pagination(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices():
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'my_data_series_with_extra_keys_{backend_key}',
                'external_id': f'_ext_id_1_{backend_key}',
                'allow_extra_fields': False,
                'backend': backend_key
            }, simulate_tenant=False)

            data = []
            for i in range(0, 10):
                dp = self.create_payload(url=data_series['data_points'], payload=lambda: {
                    'external_id': str(i),
                }, format='multipart', equality_check=False)
                self.assertEqual(dp['external_id'], str(i))
                data.append(dp)

            data.sort(key=lambda x: cast(str, x['external_id']))

            def collect_both_directions(page_size: int) -> Tuple[List[str], List[str]]:
                collected_forwards: List[str] = []
                collected_backwards: List[str] = []

                page = self.get_payload(url=data_series['data_points'] + f'?include_prev&pagesize={str(page_size)}')
                next_url = ''
                while next_url is not None:
                    cnt = 0
                    for elem in page['data']:
                        collected_forwards.append(elem['external_id'])
                        cnt += 1

                    self.assertTrue(cnt <= page_size)

                    next_url = page['next']
                    if next_url is not None:
                        page = self.get_payload(url=next_url)

                prev_url = ''
                while prev_url is not None:
                    page_data = list(page['data'])
                    page_data.reverse()

                    cnt = 0
                    for elem in page_data:
                        collected_backwards.insert(0, elem['external_id'])
                        cnt += 1

                    self.assertTrue(cnt <= page_size)

                    prev_url = page['previous']
                    if prev_url is not None:
                        page = self.get_payload(url=prev_url)

                return collected_forwards, collected_backwards

            for i in range(1, 10):
                forwards, backwards = collect_both_directions(i)
                self.assertEqual(forwards, backwards)