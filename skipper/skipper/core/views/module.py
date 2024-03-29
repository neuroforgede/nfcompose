# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Dict, Any, Optional

from rest_framework import response
from rest_framework import views
from rest_framework.request import Request

from skipper.core.views import mixin
from skipper.core.views import util as skipper_view_util


class APIOverviewView(mixin.AllowedToBrowseAPIViewMixin, views.APIView):
    listed_views: Dict[str, Any] = {}

    def get(self, request: Request, format: Optional[str] = None) -> response.Response:
        return response.Response(data={
            name: skipper_view_util.get_sub_url_view(view, request) for name, view in self.listed_views.items()
        })
