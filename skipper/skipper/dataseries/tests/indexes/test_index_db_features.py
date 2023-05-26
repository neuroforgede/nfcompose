# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from datetime import datetime, timedelta, timezone
from typing import Any, List, Tuple
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest
from skipper.dataseries.models.metamodel.index import IndexByUUID, TargetTableType, UserDefinedIndex
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType, StorageBackendType
from skipper.dataseries.storage.dynamic_sql.actions import prune_metamodel
from skipper.dataseries.tests.indexes.test_index_contracts import DATA_SERIES_BASE_URL
from skipper.core.lint import sql_cursor
from skipper.settings_env import DATA_SERIES_DYNAMIC_SQL_DB


class BaseIndexRegistryLifecycleTest(BaseViewTest):
    storage_backend_type: StorageBackendType
    expected_registered_table_types: List[TargetTableType]
    use_id: bool = False
    use_external_id: bool = False

    def _check_actual_index(self, index_name: str, target_table_name: str, ensure_deleted: bool) -> None:
        results: Any

        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(
                """
                    SELECT
                        "tablename",
                        "indexname"
                    FROM
                        "pg_catalog"."pg_indexes"
                    WHERE
                        "tablename" = %(table_name)s AND
                        "indexname" = %(index_name)s
                    ORDER BY
                        "tablename",
                        "indexname";
                """, {
                    "table_name": target_table_name,
                    "index_name": index_name
                }
            )
            results = cursor.fetchall()

            if ensure_deleted:
                self.assertEqual(
                    len(results),
                    0,
                    f'index named {index_name} on table {target_table_name} not properly deleted'
                )
            else:
                self.assertEqual(
                    len(results),
                    1,
                    f'index named {index_name} on table {target_table_name} not properly created'
                )

    def _setup(self) -> Tuple[Any, Any, Any]:
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
        index_json = self.create_payload(data_series_json['indexes'], payload={
            'name': 'my_index_name',
            'external_id': 'my_index',
            'targets': [target]
        })

        return data_series_json, fact_json, index_json

    def test_db_setup(self) -> None:
        data_series_json, fact_json, index_json = self._setup()

        index: UserDefinedIndex = UserDefinedIndex.objects.get(id=index_json['id'])
        all_registered_indexes = list(IndexByUUID.objects.all())
        registered_indexes = list(IndexByUUID.objects.filter(source_id=index.id))
        self.assertEqual(
            len(registered_indexes),
            len(self.expected_registered_table_types),
            'unexpected amount of indexes found in registry. All registered: ' + str(len(all_registered_indexes)))

        # index <==> registry entries by types
        for expected_registered_table_type in self.expected_registered_table_types:
            _found: bool = False
            for registered_index in registered_indexes:
                if expected_registered_table_type.value == registered_index.target_table_type:
                    _found = True
                    self._check_actual_index(
                        index_name=registered_index.db_name,
                        target_table_name=registered_index.target_table,
                        ensure_deleted=False
                    )
            self.assertTrue(
                _found,
                'An expected TargetTableType was not found in the index registry! Searched for: ' +
                str(expected_registered_table_type.value)
            )

    def test_db_lifecycle(self) -> None:
        num_all_registered_pre = len(list(IndexByUUID.objects.all()))
        data_series_json, fact_json, index_json = self._setup()
        index_id = UserDefinedIndex.objects.get(id=index_json['id']).id

        # grab registered indexes to later check they're deleted
        registered_name_pre_delete = {}
        registered_table_pre_delete = {}
        for key in self.expected_registered_table_types:
            idx = IndexByUUID.objects.get(source_id=index_id, target_table_type=key.value)
            registered_name_pre_delete[key.value] = idx.db_name
            registered_table_pre_delete[key.value] = idx.target_table

        self.delete_payload(url=index_json['url'])
        tenant = Tenant.objects.get(name='default_tenant')
        prune_metamodel(
            tenant_id=str(tenant.id),
            data_series_id=data_series_json['id'],
            older_than=(datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        )

        registered_indexes = list(IndexByUUID.objects.filter(source_id=index_id))
        self.assertEqual(len(registered_indexes), 0, 'indexes were not correctly deleted from registry')

        num_all_registered_post = len(list(IndexByUUID.objects.all()))
        self.assertEqual(
            num_all_registered_pre, num_all_registered_post,
            'number of entries in registry was changed by lifecycle run -> unwanted side effect'
        )

        for target_table_type in self.expected_registered_table_types:
            self._check_actual_index(
                index_name=registered_name_pre_delete[target_table_type.value],
                target_table_name=registered_table_pre_delete[target_table_type.value],
                ensure_deleted=True
            )


class IndexRegistryLifecycleTestMaterializedFlatHistByID(BaseIndexRegistryLifecycleTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    expected_registered_table_types = [TargetTableType.MATERIALIZED, TargetTableType.FLAT_HISTORY]
    use_id = True


class IndexRegistryLifecycleTestMaterializedFlatHistByExternalID(BaseIndexRegistryLifecycleTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    expected_registered_table_types = [TargetTableType.MATERIALIZED, TargetTableType.FLAT_HISTORY]
    use_external_id = True


class IndexRegistryLifecycleTestMaterializedFlatHistByBothIDs(BaseIndexRegistryLifecycleTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    expected_registered_table_types = [TargetTableType.MATERIALIZED, TargetTableType.FLAT_HISTORY]
    use_id = True
    use_external_id = True


class IndexRegistryLifecycleTestNoHistByID(BaseIndexRegistryLifecycleTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_NO_HISTORY
    expected_registered_table_types = [TargetTableType.MATERIALIZED]
    use_id = True


class IndexRegistryLifecycleTestNoHistByExternalID(BaseIndexRegistryLifecycleTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_NO_HISTORY
    expected_registered_table_types = [TargetTableType.MATERIALIZED]
    use_external_id = True


class IndexRegistryLifecycleTestNoHistByBothIDs(BaseIndexRegistryLifecycleTest):
    storage_backend_type = StorageBackendType.DYNAMIC_SQL_NO_HISTORY
    expected_registered_table_types = [TargetTableType.MATERIALIZED]
    use_id = True
    use_external_id = True


del BaseIndexRegistryLifecycleTest
