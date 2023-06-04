# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import connections
from typing import Optional

from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.contract.repository import Repository
from skipper.dataseries.storage.dynamic_sql.queries import repository
from skipper.dataseries.storage.dynamic_sql.read_only_models import data_point_accessor
from skipper.dataseries.storage.static_ds_information import BasicDataSeriesQueryInfo
from skipper.dataseries.storage.validate.contract import ReadOnlyDataPoint
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


class DynamicSQLRepository(Repository):
    def get_data_point(
            self,
            identifier: str,
            data_series_query_info: BasicDataSeriesQueryInfo
    ) -> Optional[ReadOnlyDataPoint]:
        if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value\
                or data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                cursor.execute(repository.read_only_datapoint_by_id_query(
                    data_series_query_info
                ), {
                    'data_point_id': identifier
                })
                val = cursor.fetchone()
                if val is None:
                    return None
                else:
                    return ReadOnlyDataPoint(
                        id=val[0],
                        data_series_id=data_series_query_info.data_series_id,
                        external_id=val[1]
                    )
        else:
            # FIXME: delete in 2.2.0
            return data_point_accessor(identifier=identifier, data_series_id=data_series_query_info.data_series_id)

