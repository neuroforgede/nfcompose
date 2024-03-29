# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import json
from typing import Any
from django.db.utils import IntegrityError
from rest_framework import status
from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.index import UserDefinedIndex, UserDefinedIndex_Target
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType, StorageBackendType


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class IndexCRUDContractTest(BaseViewTest):
    data_series_json: Any
    fact_json: Any
    index_json: Any

    def setUp(self) -> None:
        super().setUp()
        self.data_series_json = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)
        self.fact_json = self.create_payload(self.data_series_json['float_facts'], payload={
            'name': 'my_fact_name',
            'external_id': 'my_fact',
            'optional': True
        })
        self.index_json = self.create_payload(self.data_series_json['indexes'], payload={
            'name': 'my_index_name',
            'external_id': 'my_index',
            'targets': [{
                'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                'target_id': self.fact_json['id']
            }]
        })

    def test_crud_cycle(self) -> None:
        # Create implicit by setup

        # Read
        index: UserDefinedIndex = UserDefinedIndex.objects.get(id=self.index_json['id'])
        self.assertIsNotNone(index)
        index_json = self.get_payload(url=self.index_json['url'], payload={})
        self.assertIsNotNone(index_json)
        self.assertEqual(index_json['id'], str(index.id))

        # Update, all variations of allowed targets
        self.update_payload(url=self.index_json['url'], payload={
            'name': 'my_new_index_name',
            'external_id': 'my_index',
            'targets': [{
                'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                'target_id': self.fact_json['id']
            }]
        })
        index = UserDefinedIndex.objects.get(id=self.index_json['id'])
        self.assertEqual(index.name, 'my_new_index_name')

        self.update_payload(url=self.index_json['url'], payload={
            'name': 'my_new_index_name2',
            'external_id': 'my_index',
            'targets': [{
                'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                'target_external_id': self.fact_json['external_id']
            }]
        })
        index = UserDefinedIndex.objects.get(id=self.index_json['id'])
        self.assertEqual(index.name, 'my_new_index_name2')

        self.update_payload(url=self.index_json['url'], payload={
            'name': 'my_new_index_name3',
            'external_id': 'my_index',
            'targets': [{
                'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                'target_id': self.fact_json['id'],
                'target_external_id': self.fact_json['external_id']
            }]
        })
        index = UserDefinedIndex.objects.get(id=self.index_json['id'])
        self.assertEqual(index.name, 'my_new_index_name3')

        # Delete
        self.delete_payload(url=self.index_json['url'])
        with self.assertRaises(UserDefinedIndex.DoesNotExist):
            UserDefinedIndex.objects.get(id=self.index_json['id'])

    def test_targets_not_none(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        resp = self.client.post(
            path=data_series['indexes'],
            format='json',
            data={
                'name': 'valid_name',
                'external_id': 'valid_too',
                'targets': []
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

    def test_targets_not_incoherent(self) -> None:
        fact_json_2 = self.create_payload(self.data_series_json['float_facts'], payload={
            'name': 'my_fact_name_2',
            'external_id': 'my_fact_2',
            'optional': True
        })
        resp = self._client().post(
            path=self.data_series_json['indexes'],
            format='json',
            data={
                'name': 'broken_index',
                'external_id': 'broken_index',
                'targets': [{
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_id': self.fact_json['id'],
                    'target_external_id': fact_json_2['external_id']
                }]
            })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_index_external_id_non_mutable(self) -> None:
        resp = self.client.patch(
            path=self.index_json['url'],
            format='json',
            data={
                'external_id': 'something_else'
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

    def test_index_name_mutable(self) -> None:
        self.patch_payload(url=self.index_json['url'], payload={
            'name': 'something_else'
        })

    def test_index_targets_non_mutable_by_id(self) -> None:
        created_fact = self.create_payload(self.data_series_json['float_facts'], payload={
            'name': 'my_fact_name2',
            'external_id': 'my_fact2',
            'optional': True
        })

        resp = self.client.patch(
            path=self.index_json['url'],
            format='json',
            data={
                'targets': [{
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_id': created_fact['id']
                }]
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

    def test_index_targets_non_mutable_by_external_id(self) -> None:
        created_fact = self.create_payload(self.data_series_json['float_facts'], payload={
            'name': 'my_fact_name2',
            'external_id': 'my_fact2',
            'optional': True
        })

        resp = self.client.patch(
            path=self.index_json['url'],
            format='json',
            data={
                'targets': [{
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_external_id': created_fact['external_id']
                }]
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

    def test_index_targets_no_duplicates_rest_by_id(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)
        fact = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name2',
            'external_id': 'my_fact2',
            'optional': True
        })

        resp = self.client.post(
            path=data_series['indexes'],
            format='json',
            data={
                'name': 'my_index_name2',
                'external_id': 'my_index2',
                'targets': [{
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_id': fact['id']
                }, {
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_id': fact['id']
                }]
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

    def test_index_targets_no_duplicates_rest_by_external_id(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)
        fact = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name2',
            'external_id': 'my_fact2',
            'optional': True
        })

        resp = self.client.post(
            path=data_series['indexes'],
            format='json',
            data={
                'name': 'my_index_name2',
                'external_id': 'my_index2',
                'targets': [{
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_id': fact['id']
                }, {
                    'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                    'target_external_id': fact['external_id']
                }]
            }
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

    def test_index_targets_no_duplicates_django(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)
        fact = self.create_payload(data_series['float_facts'], payload={
            'name': 'my_fact_name2',
            'external_id': 'my_fact2',
            'optional': True
        })

        tenant = Tenant.objects.get(name='default_tenant')
        index_obj: UserDefinedIndex = UserDefinedIndex.objects.create(
            tenant=tenant,
            name="idx"
        )

        UserDefinedIndex_Target.objects.create(
            tenant=tenant,
            user_defined_index=index_obj,
            target_id=fact['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
            target_position_in_index_order=0
        )

        with self.assertRaises(IntegrityError):
            UserDefinedIndex_Target.objects.create(
                tenant=tenant,
                user_defined_index=index_obj,
                target_id=fact['id'],
                target_type=IndexableDataSeriesChildType.FLOAT_FACT.value,
                target_position_in_index_order=1
            )
