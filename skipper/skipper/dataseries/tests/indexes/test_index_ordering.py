# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.db.utils import IntegrityError
from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.index import DataSeries_UserDefinedIndex, UserDefinedIndex,\
    UserDefinedIndex_Target
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class IndexOrderTest(BaseViewTest):

    def test_index_database_order(self) -> None:
        tenant = Tenant.objects.get(name='default_tenant')

        data_series = self.create_payload(
            DATA_SERIES_BASE_URL + 'dataseries/',
            payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            },
            simulate_tenant=False
        )
        fact1 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_1',
            'external_id': 'my_fact_1',
            'optional': True
        })
        fact2 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_2',
            'external_id': 'my_fact_2',
            'optional': True
        })
        fact3 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_3',
            'external_id': 'my_fact_3',
            'optional': True
        })
        fact4 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_4',
            'external_id': 'my_fact_4',
            'optional': True
        })

        index: UserDefinedIndex = UserDefinedIndex.objects.create(
            tenant=tenant,
            name='idx'
        )

        data_series_obj: DataSeries = DataSeries.objects.get(id=data_series['id'])
        DataSeries_UserDefinedIndex.objects.create(
            tenant=tenant,
            external_id='idx',
            user_defined_index=index,
            data_series=data_series_obj
        )

        # insert targets backwards to ensure that possible ordering errors will pop up
        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index,
            target_id=fact4['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
            target_position_in_index_order=3
        )
        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index,
            target_id=fact3['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
            target_position_in_index_order=2
        )
        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index,
            target_id=fact2['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
            target_position_in_index_order=1
        )
        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index,
            target_id=fact1['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
            target_position_in_index_order=0
        )

        indexes = self.get_payload(url=data_series['indexes'])
        serial_targets = [x for x in indexes if x['external_id'] == 'idx'][0]['targets']

        self.assertEqual(serial_targets[0]['target_id'], fact1['id'])
        self.assertEqual(serial_targets[1]['target_id'], fact2['id'])
        self.assertEqual(serial_targets[2]['target_id'], fact3['id'])
        self.assertEqual(serial_targets[3]['target_id'], fact4['id'])

    def test_index_rest_order(self) -> None:

        data_series = self.create_payload(
            DATA_SERIES_BASE_URL + 'dataseries/',
            payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            },
            simulate_tenant=False
        )
        fact1 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_1',
            'external_id': 'my_fact_1',
            'optional': True
        })
        fact2 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_2',
            'external_id': 'my_fact_2',
            'optional': True
        })
        fact3 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_3',
            'external_id': 'my_fact_3',
            'optional': True
        })
        fact4 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_4',
            'external_id': 'my_fact_4',
            'optional': True
        })

        index = self.create_payload(url=data_series['indexes'], payload={
            'name': 'idx',
            'external_id': 'idx',
            'targets': [
                {
                    'target_id': fact1['id'],
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value
                },
                {
                    'target_id': fact2['id'],
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value
                },
                {
                    'target_id': fact3['id'],
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value
                },
                {
                    'target_id': fact4['id'],
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value
                }
            ]
        })

        index_obj = UserDefinedIndex.objects.get(id=index['id'])

        self.assertEqual(0, UserDefinedIndex_Target.objects.get(
            user_defined_index=index_obj, target_id=fact1['id']).target_position_in_index_order
        )
        self.assertEqual(1, UserDefinedIndex_Target.objects.get(
            user_defined_index=index_obj, target_id=fact2['id']).target_position_in_index_order
        )
        self.assertEqual(2, UserDefinedIndex_Target.objects.get(
            user_defined_index=index_obj, target_id=fact3['id']).target_position_in_index_order
        )
        self.assertEqual(3, UserDefinedIndex_Target.objects.get(
            user_defined_index=index_obj, target_id=fact4['id']).target_position_in_index_order
        )

    def test_index_database_order_unique_positions(self) -> None:
        tenant = Tenant.objects.get(name='default_tenant')

        data_series = self.create_payload(
            DATA_SERIES_BASE_URL + 'dataseries/',
            payload={
                'name': 'my_data_series_1',
                'external_id': 'external_id1'
            },
            simulate_tenant=False
        )
        fact1 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_1',
            'external_id': 'my_fact_1',
            'optional': True
        })
        fact2 = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name_2',
            'external_id': 'my_fact_2',
            'optional': True
        })

        index: UserDefinedIndex = UserDefinedIndex.objects.create(
            tenant=tenant,
            name='idx'
        )

        data_series_obj: DataSeries = DataSeries.objects.get(id=data_series['id'])
        DataSeries_UserDefinedIndex.objects.create(
            tenant=tenant,
            external_id='idx',
            user_defined_index=index,
            data_series=data_series_obj
        )

        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index,
            target_id=fact2['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
            target_position_in_index_order=0
        )

        with self.assertRaises(IntegrityError):
            UserDefinedIndex_Target.objects.create(
                tenant=tenant,
                user_defined_index=index,
                target_id=fact1['id'],
                target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
                target_position_in_index_order=0
            )
