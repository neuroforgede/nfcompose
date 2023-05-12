# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.http import HttpResponse, FileResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from typing import Union, Optional


# simple view that should be used together with something like
# nginx's auth_request module
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def app_view(request: HttpRequest, path: Optional[str] = None) -> Union[FileResponse, HttpResponse]:
    return HttpResponse(status=status.HTTP_200_OK)
