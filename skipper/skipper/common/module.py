# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any, List, Dict

from django.conf.urls import include
from django.urls import path

from skipper import modules
from skipper.common import constants, views
from skipper.core.views import module as skipper_module_views
from skipper.common.components.auth import urls as auth_urls


def get_module() -> modules.Module:
    return modules.Module.COMMON


def get_root_view_base_name() -> str:
    return constants.common_root_view_base_name


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    components_root_views = {
        'auth': constants.component_root('auth')
    }

    class CommonAPIView(skipper_module_views.APIOverviewView):
        """
        Overview for the common module
        """
        skipper_base_name = constants.common_root_view_base_name
        listed_views = components_root_views

    urls = [
        path('', CommonAPIView.as_view(), name=CommonAPIView.skipper_base_name),
        path('licensing/', views.licensing_view, name='skipper-licensing-view'),
        path('licensing/oss/', views.licensing_oss_view, name='skipper-licensing-oss-view'),
        path('auth/', include(auth_urls.get_urls()))
    ]

    return urls
