# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from compose_client.library.service.pusher import DataPointPusher
from compose_client.library.service.fetcher import ComposeDataPointFetcher
from compose_client.library.connection.client import FeatureHidingClient
from compose_client.library.models.definition.datapoint import DataPoint
from tests.base_test import BaseIntegrationTest

class TestPusher(BaseIntegrationTest):
    def setUp(self) -> None:
        super().setUp()
        self._create_data_series(
            external_id='test_data_point_pusher_ds',
            name='test_data_point_pusher_ds'
        )


    def test_DataPointPusher(self) -> None:
        push_content = [
            DataPoint(external_id='test_1', payload={}),
            DataPoint(external_id='test_2', payload={})
        ]
        pusher = DataPointPusher(client=self.client, batch_size=5)
        pusher.push(data_series_external_id='test_data_point_pusher_ds', data=push_content)
        fetcher = ComposeDataPointFetcher(
            client=self.client,
            data_series_external_id='test_data_point_pusher_ds',
            pagesize=5,
            external_ids=['test_1', 'test_2'],
            filter={},
            changes_since=None
        )
        remote_data_points = list(fetcher.fetch())
        self.assertTrue(remote_data_points == push_content)


    def test_DataPointPusher_cache(self) -> None:
        push_content = [
            DataPoint(external_id='test_1', payload={}),
            DataPoint(external_id='test_2', payload={})
        ]
        pusher = DataPointPusher(client=self.client, batch_size=5)
        pusher.push(data_series_external_id='test_data_point_pusher_ds', data=push_content, use_dataseries_definition_cache=True)
        pusher.push(data_series_external_id='test_data_point_pusher_ds', data=push_content)
        pusher.push(data_series_external_id='test_data_point_pusher_ds', data=push_content, use_dataseries_definition_cache=True)
        self.assertTrue('test_data_point_pusher_ds' in pusher._dataseries_definitions)

    def tearDown(self) -> None:
        super().tearDown()
