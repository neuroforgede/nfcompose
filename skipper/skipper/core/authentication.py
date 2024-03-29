# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from rest_framework.authentication import SessionAuthentication, TokenAuthentication, BaseAuthentication, get_authorization_header
from django.utils.translation import gettext_lazy as _
from typing import Any

from skipper.core.models.preshared_token import PreSharedToken


class DebugSessionAuthentication(SessionAuthentication):
    pass


class PossiblyJWTTokenAuthentication(BaseAuthentication):
    def authenticate(self, request: Any) -> Any:
        try:
            # first try if it is an old Token, to not spit out weird
            # errors at the end if the user used Bearer as the keyword
            from rest_framework.authentication import TokenAuthentication
            tokenAuth = TokenAuthentication()
            return tokenAuth.authenticate(request)
        except:
            # if its not an old Token, try for JWT auth
            from rest_framework_simplejwt.authentication import JWTAuthentication  # type: ignore
            jwtAuth = JWTAuthentication()
            return jwtAuth.authenticate(request)
    
    def authenticate_header(self, request: Any) -> Any:
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwtAuth = JWTAuthentication()
        return jwtAuth.authenticate_header(request)


class PreSharedTokenAuthentication(TokenAuthentication):
    keyword = 'PreSharedToken'
    model = PreSharedToken