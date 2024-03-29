# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Optional, Sequence, Any, Type

from django.middleware.csrf import get_token
from rest_framework import permissions, response, status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

from skipper.core.views import mixin


# TODO(martinb): is GenericAPIView the correct base type?
class GetCSRFTokenView(mixin.AuthenticatedViewMixin, GenericAPIView):  # type: ignore
    permission_classes = (permissions.AllowAny,)

    def get(self, request: Request, format: Optional[str] = None) -> response.Response:
        return response.Response({
            'csrftoken': get_token(request)
        }, status.HTTP_200_OK)
