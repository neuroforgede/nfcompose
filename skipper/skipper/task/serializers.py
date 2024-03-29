# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any
from rest_framework import serializers
from rest_framework.fields import CharField, JSONField


class BulkInsertTaskDataSerializer(serializers.Serializer[Any]):
    id = CharField(read_only=True)
    payload = JSONField(read_only=True)


