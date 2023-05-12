# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import transaction, connections
from typing import List, Dict, Any, cast

from skipper.core.utils.functions import chunks
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


def check_external_ids(
        external_ids: List[str],
        backend: str,
        data_series_id: str,
        data_series_query_info: DataSeriesQueryInfo
) -> List[str]:
    with transaction.atomic():
        external_ids_in_use: List[Dict[str, Any]] = []

        chunk: Any
        for chunk in chunks(external_ids, size=250):
            if backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value\
                    or backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                    sql = f"""
                        SELECT ds_dp.external_id
                        FROM {data_series_query_info.schema_name}.{data_series_query_info.main_query_table_name} ds_dp
                        WHERE ds_dp.external_id IN %s
                        AND ds_dp.deleted_at IS NULL
                    """
                    cursor.execute(
                        sql,
                        (tuple(chunk),)
                    )
                    external_ids_in_use.extend([{'external_id': x[0]} for x in cursor.fetchall()])
            else:
                external_ids_in_use.extend(cast(List[Dict[str, Any]], DataPoint.objects
                                                .filter(external_id__in=chunk)
                                                .filter(data_series_id=data_series_id)
                                                .values('external_id')))

        return [elem['external_id'] for elem in external_ids_in_use]