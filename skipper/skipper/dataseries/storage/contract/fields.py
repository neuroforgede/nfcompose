# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.db.models import Model
from rest_framework.request import Request
from typing import Dict, Any, cast

from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.dataseries.storage.contract.repository import ReadOnlyDataPoint


class DataPointHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        return {'data_series': cast(ReadOnlyDataPoint, obj).data_series_id}