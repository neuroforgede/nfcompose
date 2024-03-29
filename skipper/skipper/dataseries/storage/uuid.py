# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import hashlib
import uuid

from typing import Union


# implement different uuid strategies here, that can be set on the DataSeries object?


def gen_uuid(data_series_id: Union[uuid.UUID, str], external_id: str) -> str:
    # whenever we change this to use a different strategy, we have to make sure that
    # we check file name generation with minio data, minio is picky with special chars
    return _gen_uuid(data_series_id=data_series_id, external_id=external_id)


def _gen_uuid(data_series_id: Union[uuid.UUID, str], external_id: str) -> str:
    computed_id = hashlib.sha256(external_id.encode('UTF-8')).hexdigest()
    return f'{str(data_series_id)}-{str(computed_id)}'
