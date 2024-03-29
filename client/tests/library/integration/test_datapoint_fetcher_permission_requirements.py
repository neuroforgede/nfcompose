# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Iterable
from compose_client.library.models.definition.datapoint import DataPoint
from compose_client.library.models.definition.data_series import DataSeries
from compose_client.library.models.definition.facts import FloatFact
from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition, DataSeriesStructure, DataSeriesGroupPermissions
from compose_client.library.models.definition.group import GroupDefinition, Group, GroupPermissions
from compose_client.library.service.diff import diff_all_group_definitions, diff_all_data_series
from compose_client.library.service.pusher import GroupDefinitionDiffPusher, DataSeriesDefinitionDiffPusher, DataPointPusher
from compose_client.library.service.fetcher import ComposeDataPointFetcher
from compose_client.library.connection.client import RequestsRestClient, Credentials

from tests.base_test import BaseIntegrationTest


class MinimalRequiredPermissionsTest(BaseIntegrationTest):

    def test_minimal_required_permissions(self) -> None:
        group_definition_with_minimum_permissions = GroupDefinition(
            group=Group(name='some_group'),
            group_permissions=GroupPermissions(
                group_permissions=[
                    "dataseries.ds_get_data_point",
                    "dataseries.ds_get_data_series",
                    "dataseries.ds_get_structure_element"
                ],
            )
        )
        group_diff = diff_all_group_definitions(
            base=[],
            target=[group_definition_with_minimum_permissions]
        )
        group_definition_pusher = GroupDefinitionDiffPusher(
            client=self.client
        )
        group_definition_pusher.push(
            group_diff
        )

        ds_def = DataSeriesDefinition(
            data_series=DataSeries(
                external_id='test_ds_permissions',
                name='test_ds_permissions_name',
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
            group_permissions=[
                DataSeriesGroupPermissions(
                    name='some_group',
                    group_permissions=[
                        "dataseries.ds_get_data_point",
                        "dataseries.ds_get_data_series",
                        "dataseries.ds_get_structure_element"
                    ]
                )
            ]
        )

        ds_diffs = diff_all_data_series(
            base=[],
            target=[ds_def]
        )
        self.assertEqual(len(list(ds_diffs)), 1)

        ds_diff_pusher = DataSeriesDefinitionDiffPusher(client=self.client)
        ds_diff_pusher.push(data=ds_diffs)

        dp_pusher = DataPointPusher(client=self.client, batch_size=1)
        dp_pusher.push(
            [
                DataPoint(
                    external_id='test_dp',
                    payload={
                        'float_fact': 1.0
                    }
                )
            ],
            data_series_external_id='test_ds_permissions',
        )

        group_url = self.client.get(
            url=self.client.url('/api/common/auth/group/?name=some_group'),
        )["results"][0]["url"]
        user = self.client.post(
            url=self.client.url('/api/common/auth/user/'),
            data={
                'username': 'some_new_user',
                'password': 'some_password',
                "email": "delete.me.local@test.de",
                "groups": [
                    group_url
                ]
            }
        )

        client = RequestsRestClient(
            credentials=Credentials(
                base_url=self.client.credentials.base_url,
                user=user["fully_qualified"],
                password="some_password"
            )
        )
        fetcher = ComposeDataPointFetcher(
            client=client,
            data_series_external_id='test_ds_permissions',
            pagesize=1,
            filter=None,
            external_ids=None,
            changes_since=None
        )
        data_points = list(fetcher.fetch())
        self.assertEqual(len(data_points), 1)
        self.assertEqual(data_points[0].payload['float_fact'], 1.0)
        