# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from rest_framework.fields import JSONField
from typing import Any, Type, Dict

from skipper.core.models import default_media_storage
from skipper.dataseries.storage.contract.base import BaseDataPointSerializer
from ..models.datapoint import DisplayDataPoint
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo


class BaseDisplayDataPointSerializer(BaseDataPointSerializer):
    data_series_children_query_info: DataSeriesQueryInfo

    payload = JSONField(binary=False)

    def to_representation(self, obj: Any) -> Dict[str, Any]:
        representation: Dict[str, Any] = super().to_representation(obj)

        for external_id, value in self.data_series_children_query_info.file_facts.items():
            if external_id in representation['payload']:
                if representation['payload'][external_id] == '' or representation['payload'][external_id] is None:
                    del representation['payload'][external_id]
                else:
                    representation['payload'][external_id] = default_media_storage.url(representation['payload'][external_id])

        for external_id, value in self.data_series_children_query_info.image_facts.items():
            if external_id in representation['payload']:
                if representation['payload'][external_id] == '' or representation['payload'][external_id] is None:
                    del representation['payload'][external_id]
                else:
                    representation['payload'][external_id] = default_media_storage.url(representation['payload'][external_id])

        # do this in post, we can not handle this
        # at db level as jsonb_strip_nulls would strip all nulls from json payloads as well!
        for key in list(representation['payload'].keys()):
            if representation['payload'][key] is None:
                del representation['payload'][key]

        return representation


def display_data_point_serializer_class(
        include_versions: bool,
        data_series_children_query_info: DataSeriesQueryInfo
) -> Type[BaseDisplayDataPointSerializer]:
    _fields = ['url', 'history_url', 'id', 'external_id', 'point_in_time', 'payload']
    if include_versions:
        _fields.append('versions')

    _data_series_children_query_info = data_series_children_query_info

    class ActualSerializer(BaseDisplayDataPointSerializer):
        data_series_children_query_info = _data_series_children_query_info

        class Meta:
            model = DisplayDataPoint
            fields = _fields
            read_only_fields = _fields

    return ActualSerializer
