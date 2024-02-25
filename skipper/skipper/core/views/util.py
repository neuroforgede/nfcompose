# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.http import HttpRequest
from typing import List, Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse


def simulate_validation_error(string: str) -> Response:
    error_payload = {
        "non_field_errors": [string]
    }
    return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)


def get_sub_url_view(view_name: str, request: Request, args: List[Any] = []) -> str:
    url = str(reverse(view_name, args=args))
    if len(request.GET) == 0:
        return request.build_absolute_uri(url)
    else:
        return request.build_absolute_uri(url) + '?' + request.GET.urlencode()


def check_cors(
    request: HttpRequest,
    original_method: str
) -> bool:
    if original_method != 'OPTIONS':
        return False
    # check if it is a preflight options call by using our usual middleware
    from corsheaders.middleware import CorsMiddleware  # type: ignore
    middleware = CorsMiddleware()
    original_method_of_request = request.method
    try:
        request.method = original_method
        middleware_result = middleware.__call__(
            request
        )
        return middleware_result is not None
    finally:
        request.method = original_method_of_request
