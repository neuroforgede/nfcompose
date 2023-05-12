# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Iterable, cast
from compose_client.library.connection.client import FeatureHidingClient
from compose_client.library.models.definition.data_series import DataSeries
from compose_client.library.models.definition.facts import FloatFact
from compose_client.library.models.definition.index import Index, IndexTarget
from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition, DataSeriesStructure
from compose_client.library.models.diff.data_series import DataSeriesDefinitionDiff
from compose_client.library.service.diff import diff_all_data_series
from compose_client.library.service.pusher import DataSeriesDefinitionDiffPusher

from tests.base_test import BaseIntegrationTest

ds_def = DataSeriesDefinition(
            data_series=DataSeries(
                external_id='test_ds',
                name='test_ds_name',
                backend='DYNAMIC_SQL_NO_HISTORY',
                extra_config={
                    'auto_clean_history_after_days': -1,
                    'auto_clean_meta_model_after_days': -1
                },
                allow_extra_fields=False                
            ),
            structure=DataSeriesStructure(
                float_facts=[FloatFact(
                    external_id='float_fact',
                    name='float_fact',
                    optional=False
                )]
            )            
        )

ds_def_indexed = DataSeriesDefinition(
            data_series=DataSeries(
                external_id='test_ds',
                name='test_ds_name',
                backend='DYNAMIC_SQL_NO_HISTORY',
                extra_config={
                    'auto_clean_history_after_days': -1,
                    'auto_clean_meta_model_after_days': -1
                },
                allow_extra_fields=False                
            ),
            structure=DataSeriesStructure(
                float_facts=[FloatFact(
                    external_id='float_fact',
                    name='float_fact',
                    optional=False
                )]
            ),
            indexes=[Index(
                external_id='index',
                name='index',
                targets=[IndexTarget(
                    target_external_id='float_fact',
                    target_type='FLOAT_FACT'
                )]
            )]
        )

class IndexIntegrationTest(BaseIntegrationTest):

    def setUp(self) -> None:
        super().setUp()
        # this client simulates a target endpoint that doesn't accept indexes
        self.client = FeatureHidingClient(
            credentials=self.client.credentials,
            hidden_rest_features=['indexes']
        )
        

    def _assert_no_index_interaction(self) -> None:
        ds_index_url: str = self.client.get(self.client.url('/api/dataseries/by-external-id/dataseries/test_ds/'))['url'] + 'index/'

        client = cast(FeatureHidingClient, self.client)

        for url in client.log_get_requests:
            self.assertNotEqual(url, ds_index_url)
        for url in client.log_delete_requests:
            self.assertNotEqual(url, ds_index_url)
        for url, data in client.log_post_requests:
            self.assertNotEqual(url, ds_index_url)   
        for url, data in client.log_post_multipart_requests:
            self.assertNotEqual(url, ds_index_url)
        for url, data in client.log_patch_requests:
            self.assertNotEqual(url, ds_index_url)
        for url, data in client.log_patch_multipart_requests:
            self.assertNotEqual(url, ds_index_url)
        for url, data in client.log_put_requests:
            self.assertNotEqual(url, ds_index_url) 


    def test_client_hides_indexes_properly(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[],
            target=[ds_def]
        )
        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)

        ds = self.client.get(self.client.url('/api/dataseries/by-external-id/dataseries/test_ds/'))

        self.assertEqual(self.client.url('/api/dataseries/by-external-id/dataseries/test_ds/'), cast(FeatureHidingClient, self.client).log_get_requests[-1])
        self.assertNotIn('indexes', ds)


    def test_ds_create_index_create_ds(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[],
            target=[ds_def_indexed]
        )
        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)
        self._assert_no_index_interaction()

    
    def test_ds_delete_index_delete_ds(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[],
            target=[ds_def_indexed]
        )
        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)
        diffs = diff_all_data_series(
            base=[ds_def_indexed],
            target=[]
        )
        pusher.push(data=diffs)
        self._assert_no_index_interaction()


    def test_ds_create_index_unchanged_ds(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[],
            target=[ds_def]
        )
        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)
        diffs = diff_all_data_series(
            base=[ds_def],
            target=[ds_def_indexed]
        )
        pusher.push(data=diffs)
        self._assert_no_index_interaction()


    def test_ds_delete_index_unchanged_ds(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[],
            target=[ds_def_indexed]
        )
        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)
        diffs = diff_all_data_series(
            base=[ds_def_indexed],
            target=[ds_def]
        )
        pusher.push(data=diffs)
        self._assert_no_index_interaction()


    