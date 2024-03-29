# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Callable, Tuple, Any

from rest_framework import response
from rest_framework import status


class HttpError(Exception):
    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class Http400(HttpError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class Http404(HttpError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class Http409(HttpError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


class Http500(HttpError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


def wrap_exception(func: 'Callable[..., Tuple[Any, Any]]', **kwargs: Any) -> response.Response:
    try:
        data, status = func(kwargs)
        return response.Response(data=data, status=status)
    except HttpError as error:
        return response.Response(status=error.status, data=error.message)
