# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from datetime import datetime, timedelta, timezone
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BASE_URL, BaseViewTest
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType, StorageBackendType
from skipper.dataseries.storage.dynamic_sql.actions import nuke_data_series
from skipper.dataseries.tests.indexes.test_index_contracts import DATA_SERIES_BASE_URL


class BaseIndexPruneDataseriesTest(BaseViewTest):
    storage_backend_type: StorageBackendType
    use_id: bool = False
    use_external_id: bool = False

    def test_index_prune_whole_data_series(self) -> None:
        data_series_json = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1',
            'backend': self.storage_backend_type.value
        }, simulate_tenant=False)
        fact_json = self.create_payload(data_series_json['float_facts'], payload={
            'name': 'my_fact_name',
            'external_id': 'my_fact',
            'optional': True
        })
        target = {
            'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value
        }
        if self.use_id:
            target['target_id'] = fact_json['id']
        if self.use_external_id:
            target['target_external_id'] = fact_json['external_id']
        self.create_payload(data_series_json['indexes'], payload={
            'name': 'my_index_name',
            'external_id': 'my_index',
            'targets': [target]
        })

        self.delete_payload(data_series_json['url'])

        tenant = Tenant.objects.get(name='default_tenant')
        nuke_data_series(
            tenant_id=str(tenant.id),
            data_series_id=data_series_json['id'],
            older_than=(datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        )

        self._client().post(
            path=BASE_URL + 'api/dataseries/prune/dataseries/',
            format='json',
            data={
                'older_than': (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
                'accept': True
            }
        )

class IndexRegistryLifecycleTestMaterializedFlatHistByID(BaseIndexPruneDataseriesTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    use_id = True


class IndexRegistryLifecycleTestMaterializedFlatHistByExternalID(BaseIndexPruneDataseriesTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    use_external_id = True


class IndexRegistryLifecycleTestMaterializedFlatHistByBothIDs(BaseIndexPruneDataseriesTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    use_id = True
    use_external_id = True


class IndexRegistryLifecycleTestNoHistByID(BaseIndexPruneDataseriesTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_NO_HISTORY
    use_id = True


class IndexRegistryLifecycleTestNoHistByExternalID(BaseIndexPruneDataseriesTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_NO_HISTORY
    use_external_id = True


class IndexRegistryLifecycleTestNoHistByBothIDs(BaseIndexPruneDataseriesTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_NO_HISTORY
    use_id = True
    use_external_id = True


del BaseIndexPruneDataseriesTest
