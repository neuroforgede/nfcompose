# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

# from enum import Enum
from compose_client.library.models.definition.datapoint import DataPoint
from compose_client.library.models.operation.general import OperationType
from dataclasses import dataclass

@dataclass
class DataPointOperation():
     operation_type: OperationType
     datapoint: DataPoint
