# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any, List, Dict

from django.conf.urls import include
from django.urls import path, re_path
from rest_framework import routers

from skipper import modules
from skipper.core import constants
from skipper.core.feature_flags import get_feature_flag
from skipper.core.utils.router import DefaultRouter
from skipper.core.views import module as skipper_module_views, mixin
from skipper.core.components.user import views as user_views
from skipper.core.components.user.user_permissions import UserPermissionsView
from skipper.core.components.tenant import views as tenant_views
from skipper.core.components.tenant.tenant_users import TenantUserViewSet


def get_module() -> modules.Module:
    return modules.Module.CORE


def get_root_view_base_name() -> str:
    return constants.core_root_view_base_name


class CoreAPIView(mixin.AllowedToBrowseAPIViewMixin, routers.APIRootView):
    pass


class CoreRouter(DefaultRouter):
    APIRootView = CoreAPIView

    # only needed for component style modules
    # root_view_name = constants.data_root_view_base_name
    root_view_name = constants.core_root_view_base_name

    skipper_base_name = constants.core_root_view_base_name


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    components_root_views: Dict[str, str]= {}
    
    if get_feature_flag("compose.core.tenant"):
        components_root_views = {
            'tenant': constants.core_tenant_view_set_name + '-list',
            **components_root_views
        }

    if get_feature_flag("compose.core.user"):
        components_root_views = {
            'user': constants.core_user_view_set_name + '-list',
            **components_root_views
        }

    class CoreAPIView(skipper_module_views.APIOverviewView):
        """
        Overview for the core module
        """
        skipper_base_name = constants.core_root_view_base_name
        listed_views = components_root_views

    urls: List[Any] = [
        path('', CoreAPIView.as_view(), name=CoreAPIView.skipper_base_name),
        # re_path(
        #     r'^group/(?P<pk>[^/.]+)/permission/',
        #     GroupPermissionsView.as_view(),
        #     name=GroupPermissionsView.skipper_base_name
        # ),
    ]
    
    router = CoreRouter()
    
    if get_feature_flag("compose.core.tenant"):
        router.register(
            r'tenant',
            tenant_views.TenantViewSet,
            basename=tenant_views.TenantViewSet.skipper_base_name 
        )
    if get_feature_flag("compose.core.tenant.tenant_user"):
        router.register(
            r'tenant/(?P<tenant_id>[^/.]+)/user',
            TenantUserViewSet,
            basename=TenantUserViewSet.skipper_base_name
        )
    if get_feature_flag("compose.core.user"):
        router.register(
            r'user',
            user_views.UserViewSet,
            basename=user_views.UserViewSet.skipper_base_name
        )
        urls.append(
            re_path(
                r'^user/(?P<pk>[^/.]+)/permission/',
                UserPermissionsView.as_view(),
                name=UserPermissionsView.skipper_base_name
            )
        )

    urls += router.urls

    return urls
