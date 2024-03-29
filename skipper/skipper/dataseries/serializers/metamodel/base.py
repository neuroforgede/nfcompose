# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Tuple

from rest_framework import serializers

from skipper.core.serializers.base import BaseSerializer


class DataSeriesBaseSerializer(BaseSerializer):
    name = serializers.CharField(max_length=256)

    def get_validators(self) -> Any:
        """
        Determine the set of validators to use when instantiating serializer.
        """
        return super().get_validators()


def _base_serializer_fields(fields: Tuple = ()) -> Tuple:  # type: ignore
    return ('url', 'id', 'external_id', 'point_in_time', 'last_modified_at',) + fields


def _named_serializer_fields(fields: Tuple = ()) -> Tuple:  # type: ignore
    return _base_serializer_fields(('name',) + fields)