# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Protocol, Optional, Union, NamedTuple
from uuid import UUID

from skipper.dataseries.storage.static_ds_information import BasicDataSeriesQueryInfo


class ReadOnlyDataPoint(NamedTuple):
    id: str
    data_series_id: Union[str, UUID]
    external_id: str


class Repository(Protocol):
    def get_data_point(
            self,
            identifier: str,
            data_series_query_info: BasicDataSeriesQueryInfo
    ) -> Optional[ReadOnlyDataPoint]: ...

