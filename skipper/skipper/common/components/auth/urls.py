# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, List, Dict, Union

from django.conf.urls import include
from django.shortcuts import redirect
from django.urls import path, re_path
from django.http.response import HttpResponsePermanentRedirect, HttpResponseRedirect
from rest_framework import routers
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework.generics import GenericAPIView

from skipper import settings
from skipper.common import constants
from skipper.common.components.auth import views
from skipper.common.components.auth.views import GroupPermissionsView, UserPermissionsView
from skipper.core.utils.router import DefaultRouter
from skipper.core.views import mixin

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView, TokenBlacklistView # type: ignore

from skipper.core.views.util import get_sub_url_view


class CommonAuthAPIView(mixin.AllowedToBrowseAPIViewMixin, routers.APIRootView):
    api_root_dict: Dict[str, str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)  # type: ignore

        self.api_root_dict['authtoken'] = 'auth-token'
        self.api_root_dict['check'] = 'login-check'
        self.api_root_dict['csrftoken'] = 'csrf-token'

        self.api_root_dict['jwt'] = constants.common_auth_jwt_root_view_name


class CommonAuthRouter(DefaultRouter):
    APIRootView = CommonAuthAPIView
    root_view_name = constants.common_auth_root_view_base_name


# TODO(martinb): is this the correct base class?
class JWTView(
    GenericAPIView # type: ignore
):
    """
    The JWT Token API
    """
    permission_classes = ()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({
            "obtain": get_sub_url_view(constants.common_auth_jwt_obtain_pair_view_name, request),
            "refresh": get_sub_url_view(constants.common_auth_jwt_refresh_view_name, request),
            "verify": get_sub_url_view(constants.common_auth_jwt_verify_view_name, request),
            "blacklist": get_sub_url_view(constants.common_auth_jwt_blacklist_view_name, request)
        })
    


def get_urls() -> List[Any]:
    def redirect_after_login(request: Request) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect]:
        response = redirect('/' + settings.ROOT_API_PATH + '')
        return response

    urls = [
        path('success', redirect_after_login),
        # override the login views that Django RESTFramework supplies us with but instead use our
        # customized ones based on the originals
        re_path(r'^login/$', views.SkipperLoginView.as_view(template_name='rest_framework/login.html'), name='login'),
        re_path(r'^logout/$', views.SkipperLogoutView.as_view(), name='logout'),
        path('', include('rest_framework.urls', namespace='rest_framework')),
        path(r'authtoken/', views.TokenAuthView.as_view(), name='auth-token'),
        path(
            r'check/', views.UserLoggedInCheckView.as_view(),
            name='login-check'
        ),
        path(
            r'csrftoken/', views.GetCSRFTokenView.as_view(),
            name='csrf-token'
        ),
        re_path(
            r'^group/(?P<pk>[^/.]+)/permission/',
            GroupPermissionsView.as_view(),
            name=GroupPermissionsView.skipper_base_name
        ),
        re_path(
            r'^user/(?P<pk>[^/.]+)/permission/',
            UserPermissionsView.as_view(),
            name=UserPermissionsView.skipper_base_name
        ),
        path('jwt', JWTView.as_view(), name=constants.common_auth_jwt_root_view_name),
        path('jwt/obtain/', TokenObtainPairView.as_view(), name=constants.common_auth_jwt_obtain_pair_view_name),
        path('jwt/refresh/', TokenRefreshView.as_view(), name=constants.common_auth_jwt_refresh_view_name),
        path('jwt/verify/', TokenVerifyView.as_view(), name=constants.common_auth_jwt_verify_view_name),
        path('jwt/blacklist/', TokenBlacklistView.as_view(), name=constants.common_auth_jwt_blacklist_view_name)
    ]

    router = CommonAuthRouter()
    router.register(
        r'user',
        views.UserViewSet,
        basename=views.UserViewSet.skipper_base_name
    )
    router.register(
        r'group',
        views.GroupViewSet,
        basename=views.GroupViewSet.skipper_base_name
    )

    urls += router.urls
    return urls
