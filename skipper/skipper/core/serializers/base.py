# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import List, Dict, Any
from urllib.parse import urlencode

from rest_framework import serializers
from rest_framework.reverse import reverse


class BaseSerializer(serializers.HyperlinkedModelSerializer):
    sub_views: List[Dict[str, str]] = []

    def to_representation(self, obj: Any) -> Any:
        representation = super().to_representation(obj)
        for _sub_view in self.sub_views:
            representation[_sub_view['sub_path']] = self.get_sub_url(
                view_name=_sub_view['view_name'],
                args=[obj.id]
            )

        return representation

    def get_sub_url(self, view_name: str, args: List[Any]) -> str:
        url = str(reverse(view_name, args=args))
        request = self.context['request']
        if 'format' in request.GET:
            return str(request.build_absolute_uri(url)) + '?' + urlencode({'format': request.GET['format']})
        else:
            return str(request.build_absolute_uri(url))
