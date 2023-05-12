# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.conf.urls import include
from django.urls import path
from rest_framework import routers
from typing import Any, List, Dict

from skipper import modules
from skipper.core.utils.router import DefaultRouter
from skipper.core.views import mixin
from skipper.core.views.module import APIOverviewView
from skipper.health import constants
from skipper.health.views import SubSystemHealthViewSet


def get_module() -> modules.Module:
    return modules.Module.HEALTH


def get_root_view_base_name() -> str:
    return constants.root_view_base_name


class HealthAPIView(mixin.AllowedToBrowseAPIViewMixin, routers.APIRootView):
    """
    The Health API
    """


class HealthRouter(DefaultRouter):
    APIRootView = HealthAPIView

    # only needed for component style modules
    # root_view_name = constants.data_root_view_base_name
    root_view_name = constants.root_view_base_name

    skipper_base_name = constants.root_view_base_name


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    _listed_views: Dict[str, Any] = {
        'subsystem': SubSystemHealthViewSet.skipper_base_name + '-list'
    }

    class HealthAPIView(APIOverviewView):
        """
        Overview for the Health API
        """
        skipper_base_name = constants.root_view_base_name
        listed_views = _listed_views

    router = HealthRouter()

    router.register(
        r'subsystem',
        SubSystemHealthViewSet,
        basename=SubSystemHealthViewSet.skipper_base_name)

    urls = [
        path('', HealthAPIView.as_view(), name=HealthAPIView.skipper_base_name),
        path(
            '',
            include(router.urls)
        ),
    ]

    return urls
