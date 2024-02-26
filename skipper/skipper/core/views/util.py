# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.http import HttpRequest, HttpResponse
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


def check_preflight(request: HttpRequest) -> HttpResponse | None:
    """
    Generate a response for CORS preflight requests.
    """
    if (
        request.method == "OPTIONS"
        and "access-control-request-method" in request.headers
    ):
        return HttpResponse(headers={"content-length": "0"})
    return None


def check_cors(
    request: HttpRequest,
    original_method: str
) -> bool:
    if original_method != 'OPTIONS':
        return False
    original_method_of_request = request.method
    try:
        request.method = original_method
        middleware_result = check_preflight(
            request
        )
        return middleware_result is not None
    finally:
        request.method = original_method_of_request
