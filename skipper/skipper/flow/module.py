# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.conf.urls import include
from django.urls import path, re_path
from rest_framework import routers
from typing import Any, List, Dict

from skipper import modules
from skipper.core.utils.router import DefaultRouter
from skipper.core.views import mixin
from skipper.core.views.module import APIOverviewView
from skipper.flow import constants, healthcheck
from skipper.flow.admin import HttpEndpointAdmin, EngineAdmin
from skipper.flow.models import HttpEndpoint, Engine
from skipper.flow.views.engine_crud import EngineViewSet, EnginePermissionUserViewSet, EnginePermissionGroupViewSet
from skipper.flow.views.engine_access import EngineAccessView, NginXEngineAccessView
from skipper.flow.views.engine_secret import EngineSecretView
from skipper.flow.views.flow_options import flow_options_view
from skipper.flow.views.http_endpoint_crud import HttpEndpointViewSet, HttpEndpointPermissionUserViewSet, \
    HttpEndpointPermissionGroupViewSet
from skipper.flow.views.system_engine_access import system_engine_access_view
from skipper.flow.views.flow_impl import flow_impl_view
from skipper.flow.views.flow_public_impl import flow_impl_public_view
from django.contrib import admin

admin.site.register(HttpEndpoint, HttpEndpointAdmin)
admin.site.register(Engine, EngineAdmin)


def get_module() -> modules.Module:
    return modules.Module.FLOW


def get_root_view_base_name() -> str:
    return constants.root_view_base_name


class FlowAPIView(mixin.AllowedToBrowseAPIViewMixin, routers.APIRootView):
    """
    The Data Series API
    """


class FlowRouter(DefaultRouter):
    APIRootView = FlowAPIView

    # only needed for component style modules
    # root_view_name = constants.data_root_view_base_name
    root_view_name = constants.root_view_base_name

    skipper_base_name = constants.root_view_base_name


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    _listed_views: Dict[str, Any] = {
        'system_engine': constants.system_engine_access_base_name + '-root',
        'engine': constants.engine_view_base_name + '-list',
        'http_endpoint': constants.http_endpoint_view_base_name + '-list'
    }

    healthcheck.register_health_checks()

    class FlowAPIView(APIOverviewView):
        """
        Overview for the Flow API
        """
        skipper_base_name = constants.root_view_base_name
        listed_views = _listed_views

    router = FlowRouter()

    router.register(
        r'engine',
        EngineViewSet,
        basename=EngineViewSet.skipper_base_name)

    router.register(
        r'engine/(?P<parent1>[^/.]+)/permission/user',
        EnginePermissionUserViewSet,
        basename=EnginePermissionUserViewSet.skipper_base_name
    )

    router.register(
        r'engine/(?P<parent1>[^/.]+)/permission/group',
        EnginePermissionGroupViewSet,
        basename=EnginePermissionGroupViewSet.skipper_base_name
    )

    router.register(
        r'httpendpoint',
        HttpEndpointViewSet,
        basename=HttpEndpointViewSet.skipper_base_name)

    router.register(
        r'httpendpoint/(?P<parent1>[^/.]+)/permission/user',
        HttpEndpointPermissionUserViewSet,
        basename=HttpEndpointPermissionUserViewSet.skipper_base_name
    )

    router.register(
        r'httpendpoint/(?P<parent1>[^/.]+)/permission/group',
        HttpEndpointPermissionGroupViewSet,
        basename=HttpEndpointPermissionGroupViewSet.skipper_base_name
    )

    urls = [
        path('', FlowAPIView.as_view(), name=FlowAPIView.skipper_base_name),
        path(
            'engine/access-auth/',
            NginXEngineAccessView.as_view(),
            name=NginXEngineAccessView.skipper_base_name
        ),
        re_path(
            r'^engine/(?P<pk>[^/.]+)/secret/',
            EngineSecretView.as_view(),
            name=EngineSecretView.skipper_base_name
        ),
        re_path(
            r'^engine/(?P<pk>[^/.]+)/access/',
            EngineAccessView.as_view(),
            name=EngineAccessView.skipper_base_name
        ),
        path('options/', flow_options_view, name=constants.flow_options_base_name + '-root'),
        path('system/engine/access/', system_engine_access_view, name=constants.system_engine_access_base_name + '-root'),
        path('impl/', flow_impl_view, name=constants.node_red_base_impl_base_name + '-root'),
        path('public/impl/', flow_impl_public_view, name=constants.node_red_base_public_impl_base_name + '-root'),
        path(
            '',
            include(router.urls)
        ),
    ]
    return urls
