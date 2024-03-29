# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Any
from rest_framework import status
from skipper.core.lint import sql_cursor
from skipper.core.tests.base import BaseViewTest
from skipper.dataseries.models.metamodel.index import IndexByUUID, TargetTableType
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType, StorageBackendType
from skipper.dataseries.tests.indexes.test_index_contracts import DATA_SERIES_BASE_URL
from skipper.settings_env import DATA_SERIES_DYNAMIC_SQL_DB


class IndexBackendMigrationTest(BaseViewTest):
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

    def test_backend_migration_flat_to_no_hist(self) -> None:
        data_series_json = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1',
            'backend': StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value
        }, simulate_tenant=False)
        fact_json = self.create_payload(data_series_json['float_facts'], payload={
            'name': 'my_fact_name',
            'external_id': 'my_fact',
            'optional': True
        })
        index_json = self.create_payload(data_series_json['indexes'], payload={
            'name': 'my_index_name',
            'external_id': 'my_index',
            'targets': [{
                'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                'target_id': fact_json['id']
            }]
        })

        idx_mat = IndexByUUID.objects.get(
            source_id=index_json['id'],
            target_table_type=TargetTableType.MATERIALIZED.value
        )
        idx_mat_name = idx_mat.db_name
        idx_mat_target_table = idx_mat.target_table
        idx_fhist = IndexByUUID.objects.get(
            source_id=index_json['id'],
            target_table_type=TargetTableType.FLAT_HISTORY.value
        )
        idx_fhist_name = idx_fhist.db_name
        idx_fhist_target_table = idx_fhist.target_table

        self._check_actual_index(
            index_name=idx_mat_name,
            target_table_name=idx_mat_target_table,
            ensure_deleted=False
        )
        self._check_actual_index(
            index_name=idx_fhist_name,
            target_table_name=idx_fhist_target_table,
            ensure_deleted=False
        )

        # migrate
        resp = self._client().patch(
            path=data_series_json['url'],
            format='json',
            data={'backend': StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self._check_actual_index(
            index_name=idx_mat_name,
            target_table_name=idx_mat_target_table,
            ensure_deleted=False
        )
        self._check_actual_index(
            index_name=idx_fhist_name,
            target_table_name=idx_fhist_target_table,
            ensure_deleted=True
        )

    def test_backend_migration_no_hist_to_flat(self) -> None:
        data_series_json = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1',
            'backend': StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value
        }, simulate_tenant=False)
        fact_json = self.create_payload(data_series_json['float_facts'], payload={
            'name': 'my_fact_name',
            'external_id': 'my_fact',
            'optional': True
        })
        index_json = self.create_payload(data_series_json['indexes'], payload={
            'name': 'my_index_name',
            'external_id': 'my_index',
            'targets': [{
                'target_type': IndexableDataSeriesChildType.FLOAT_FACT.value,
                'target_id': fact_json['id']
            }]
        })

        idx_mat = IndexByUUID.objects.get(
            source_id=index_json['id'],
            target_table_type=TargetTableType.MATERIALIZED.value
        )
        idx_mat_name = idx_mat.db_name
        idx_mat_target_table = idx_mat.target_table

        self._check_actual_index(
            index_name=idx_mat_name,
            target_table_name=idx_mat_target_table,
            ensure_deleted=False
        )

        # migrate
        resp = self._client().patch(
            path=data_series_json['url'],
            format='json',
            data={'backend': StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        idx_fhist = IndexByUUID.objects.get(
            source_id=index_json['id'],
            target_table_type=TargetTableType.FLAT_HISTORY.value
        )
        idx_fhist_name = idx_fhist.db_name
        idx_fhist_target_table = idx_fhist.target_table

        self._check_actual_index(
            index_name=idx_mat_name,
            target_table_name=idx_mat_target_table,
            ensure_deleted=False
        )
        self._check_actual_index(
            index_name=idx_fhist_name,
            target_table_name=idx_fhist_target_table,
            ensure_deleted=False
        )
