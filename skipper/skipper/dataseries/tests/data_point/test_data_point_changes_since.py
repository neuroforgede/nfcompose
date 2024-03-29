# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import io

import datetime
from django.utils import timezone
from urllib.parse import quote as urlquote
from typing import Any, Dict

from PIL import Image as PIL_Image  # type: ignore

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

from rest_framework import status

from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract import StorageBackendType

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BaseChangesSinceTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    data_series: Dict[str, Any]

    backend: str

    def setUp(self) -> None:
        super().setUp()

        self.data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1',
            'backend': self.backend
        }, simulate_tenant=False)

    def test_changes_since_insert(self) -> None:

        def check(time: datetime.datetime, expected_cnt: int) -> None:
            changes_since_after_create = self.get_payload(
                url=f"{self.data_series['data_points']}?changes_since={urlquote(str(time.isoformat()))}"
            )
            self.assertEqual(len(changes_since_after_create['data']), expected_cnt)

            changes_since_after_create_count = self.get_payload(
                url=f"{self.data_series['data_points']}?changes_since={urlquote(str(time.isoformat()))}&count"
            )
            self.assertEqual(changes_since_after_create_count['count'], expected_cnt)

        now = dbtime.now()

        check(now, 0)

        created = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": 'should_fail',
                "payload": {}
            }, format='json'
        ).json()

        now_after_create = dbtime.now()

        self.assertNotEqual(now, now_after_create)

        check(now, 1)
        check(now_after_create, 0)

        # update with put, should now be there
        updated_put = self.client.put(
            path=created['url'],
            data={
                f"external_id": 'should_fail',
                "payload": {}
            }, format='json'
        ).json()

        now_after_put = dbtime.now()

        check(now, 1)
        check(now_after_create, 1)
        check(now_after_put, 0)

        updated_patch = self.client.patch(
            path=created['url'],
            data={
                f"external_id": 'should_fail',
                "payload": {}
            }, format='json'
        ).json()

        now_after_patch = dbtime.now()

        check(now, 1)
        check(now_after_create, 1)
        check(now_after_put, 1)
        check(now_after_patch, 0)


class MaterializedChangesSinceTest(BaseChangesSinceTest):
    backend = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value


del BaseChangesSinceTest

