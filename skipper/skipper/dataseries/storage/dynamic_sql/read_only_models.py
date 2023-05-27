# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from uuid import UUID

from typing import Optional, Union

from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint
from skipper.dataseries.storage.validate.contract import ReadOnlyDataPoint

# DEPRECATED, only for backends that have been deleted.
# DELETE this in 2.2.0

def data_point_accessor(
        identifier: str,
        data_series_id: Union[str, UUID]
) -> Optional[ReadOnlyDataPoint]:
    qs = DataPoint.objects.filter(
        data_series_id=data_series_id,
        id=identifier
    )
    if len(qs) > 0:
        _dp: DataPoint = qs[0]
        return ReadOnlyDataPoint(
            id=_dp.id,
            data_series_id=_dp.data_series_id,
            external_id=_dp.external_id
        )
    else:
        return None