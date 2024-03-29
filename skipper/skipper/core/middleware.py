# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from django.http import HttpRequest
from typing import Any, cast, Optional

from django.contrib.auth import get_user
from django_multitenant.utils import set_current_tenant  # type: ignore

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local  # type: ignore


_thread_locals = local()


def check_basic_auth_for_user(request: Any) -> Any:
    from rest_framework.authentication import BasicAuthentication
    authenticator = BasicAuthentication()
    try:
        _user, _ = authenticator.authenticate(request)  # type: ignore
        return _user
    except:
        return None


def check_preshared_token_auth_for_user(request: Any) -> Any:
    from skipper.core.authentication import PreSharedTokenAuthentication
    authenticator = PreSharedTokenAuthentication()
    try:
        _user, _ = authenticator.authenticate(request)  # type: ignore
        return _user
    except:
        return None


def check_token_auth_for_user(request: Any) -> Any:
    from skipper.core.authentication import PossiblyJWTTokenAuthentication
    authenticator = PossiblyJWTTokenAuthentication()
    try:
        _user, _ = authenticator.authenticate(request)  # type: ignore
        return _user
    except:
        return None


def check_session_auth_for_user(request: Any) -> Any:
    from rest_framework.authentication import SessionAuthentication
    authenticator = SessionAuthentication()
    try:
        _user, _ = authenticator.authenticate(request)  # type: ignore
        return _user
    except:
        return None

class TenantFromUserMiddleware(object):
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        set_current_tenant(None)
        from skipper.core.models.tenant import Tenant, Tenant_User
        from opentelemetry import trace  # type: ignore

        tracer = trace.get_tracer(__name__)

        user = get_user(request)

        if user is None or user.is_anonymous:
            user = check_token_auth_for_user(request)

        if user is None or user.is_anonymous:
            user = check_preshared_token_auth_for_user(request)

        if user is None or user.is_anonymous:
            user = check_basic_auth_for_user(request)

        if user is None or user.is_anonymous:
            user = check_session_auth_for_user(request)

        _user_name: Optional[str] = None
        _tenant_name: Optional[str] = None
        if user is None or user.is_anonymous:
            set_current_tenant(None)
        else:
            _user_name = cast(User, user).username
            tenant_mapping = Tenant_User.objects.filter(
                user=cast(User, user)
            ).all()
            if len(tenant_mapping) > 0:
                _tenant = tenant_mapping[0].tenant
                _tenant_name = _tenant.name
                if _tenant.deleted_at is None:
                    set_current_tenant(_tenant)

        with tracer.start_as_current_span(self.__class__.__module__ + '.' + self.__class__.__qualname__, attributes={
            **({"skipper.core.user": _user_name} if _user_name is not None else {}),
            **({"skipper.core.tenant": _tenant_name} if _tenant_name is not None else {})
        }):
            response = self.get_response(request)

        set_current_tenant(None)
        return response


class TrackCurrentRequestMiddleware(object):
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        set_current_request(request)

        response = self.get_response(request)

        set_current_request(None)
        return response


def set_current_request(request: Optional[HttpRequest]) -> None:
    setattr(_thread_locals, '__current_request', request)


def get_current_request() -> HttpRequest:
    return cast(HttpRequest, getattr(_thread_locals, '__current_request', None))
