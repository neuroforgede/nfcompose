# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Iterable
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

ds_def_updated = DataSeriesDefinition(
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
                ),
                FloatFact(
                    external_id='float_fact_2',
                    name='float_fact_2',
                    optional=False
                )]
            ),
            indexes=[Index(
                external_id='index',
                name='index',
                targets=[
                    IndexTarget(
                        target_external_id='float_fact',
                        target_type='FLOAT_FACT'
                    ),
                    IndexTarget(
                        target_external_id='float_fact_2',
                        target_type='FLOAT_FACT'
                    )
                ]
            )]
        )

class IndexIntegrationTest(BaseIntegrationTest):

    def _push(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[],
            target=[ds_def]
        )
        self.assertEqual(len(list(diffs)), 1)
        diff: DataSeriesDefinitionDiff = list(diffs)[0]
        self.assertEqual(len(diff.indexes), 1)
        self.assertEqual(len(diff.structure.float_facts), 1)

        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)
        
    def _update(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[ds_def],
            target=[ds_def_updated]
        )
        self.assertEqual(len(list(diffs)), 1)
        diff: DataSeriesDefinitionDiff = list(diffs)[0]
        self.assertEqual(len(diff.indexes), 2)
        self.assertEqual(len(diff.structure.float_facts), 1)

        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)

    def _delete(self) -> None:
        diffs: Iterable[DataSeriesDefinitionDiff] = diff_all_data_series(
            base=[ds_def_updated],
            target=[]
        )
        self.assertEqual(len(list(diffs)), 1)
        diff: DataSeriesDefinitionDiff = list(diffs)[0]
        self.assertEqual(len(diff.indexes), 0)
        self.assertEqual(len(diff.structure.float_facts), 0)

        pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        pusher.push(data=diffs)

    def test_push_definition(self) -> None:
        self._push()

    def test_update_definition(self) -> None:
        self._push()
        self._update()

    def test_delete_definition(self) -> None:
        self._push()
        self._update()
        self._delete()