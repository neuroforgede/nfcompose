# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from uuid import UUID

from typing import Optional, NamedTuple, Dict, Any, Union, Protocol

from skipper.dataseries.storage.contract.repository import ReadOnlyDataPoint
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo


class DataPointAccessor(Protocol):
    def __call__(
            self,
            identifier: str,
            data_series_id: Union[str, UUID]
     ) -> Optional[ReadOnlyDataPoint]: ...


class ValidationRequest(NamedTuple):
    data_point_id: Optional[str]
    data_point_relation_info: DataSeriesQueryInfo
    partial: bool
    bulk_insert: bool
    external_id_as_dimension_identifier: bool
    data_point_accessor: DataPointAccessor


class DataPointValidation(Protocol):
    def __call__(
            self,
            data: Dict[str, Any],
            request: ValidationRequest
    ) -> Dict[str, Any]: ...
