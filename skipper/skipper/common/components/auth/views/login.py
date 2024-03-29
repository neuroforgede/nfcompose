# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Optional, Set, Any

from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest
from rest_framework import response, status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

from skipper import settings
from skipper.core.models.tenant import AllowedLoginRedirectHost, Tenant
from skipper.core.utils.tenant import get_tenant_from_hostname
from skipper.core.views import mixin


# TODO(martinb): is GenericAPIView the correct base type?
class UserLoggedInCheckView(mixin.AuthenticatedViewMixin, GenericAPIView):  # type: ignore

    def get(self, request: Request, format: Optional[str] = None) -> response.Response:
        return response.Response({
            'username': request.user.username,
            'groups': [group.name for group in request.user.groups.all()],  # type: ignore
            'staff': request.user.is_staff,
            'superuser': request.user.is_superuser
        }, status.HTTP_200_OK)


# customize the login view in a way that allowed to redirect to external
# hosts (only whitelisted ones!)
class ExternalSuccessURLAllowedHostsMixin:
    request: HttpRequest
    _debug = settings.DEBUG

    def get_success_url_allowed_hosts(self) -> Set[str]:
        allowed_hosts = {self.request.get_host(), *settings.LOGIN_REDIRECT_ALLOWED_HOSTS}
        tenant_from_hostname: Optional[Tenant] = get_tenant_from_hostname(self.request.get_host())
        if tenant_from_hostname is not None:
            if self._debug:
                print('found tenant', tenant_from_hostname.name)
            for _allowed_host in AllowedLoginRedirectHost.objects.filter(tenant=tenant_from_hostname).all():
                allowed_hosts.add(_allowed_host.host)
                if self._debug:
                    print('added allowed host', _allowed_host.host)
        if self._debug:
            print('allowed hosts', allowed_hosts)
        return allowed_hosts


class SkipperLoginView(ExternalSuccessURLAllowedHostsMixin, LoginView):
    pass


class SkipperLogoutView(ExternalSuccessURLAllowedHostsMixin, LogoutView):
    pass
