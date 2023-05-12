# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from datetime import timedelta
from typing import Any

from rest_framework_simplejwt.tokens import AccessToken  # type: ignore
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from skipper.core.views import mixin


class TokenAuthView(
    mixin.AuthenticatedViewMixin,
    mixin.HttpErrorAwareCreateModelMixin,
    GenericAPIView  # type: ignore
):
    """
    View to fetch an Auth Token for a user.

    Returns JWT Tokens for use with the API with validity of 2 hours.
        (this may change in the future, please refresh more often)

    Note: Currently, work is being done on the JWT endpoints, which,
          once stable, will supersede this endpoint.
    """
    permission_classes = ()
    serializer_class = AuthTokenSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        access_token = AccessToken.for_user(user)

        # use a bit longer lifecycle of max 2 hours in this endpoint
        # to not have old integrations break. This also currently includes
        # all compose clients using the python client library
        access_token.set_exp(lifetime=timedelta(hours=2))

        return Response({
            'token': str(access_token)
        })
        
