# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import abc
import sys
from dataclasses import dataclass
from typing import Dict, cast, Any, Optional

import requests
from requests import Session
from requests.exceptions import HTTPError

from library import env
from library.types import JSONType


USER_AGENT = 'integration_test compose 2.2.4'


class APIClient(abc.ABC):
    """
    central class, abstracts reading, writing, etc
    into simple methods. Implementations might be REST clients,
    mock clients, etc.

    This does not abstract reading and writing to disk
    as on disk we do not have a proper concept of pagination
    which this interface is usually used together with
    """
    def url(self, path: str) -> str: ...

    def get(self, url: str) -> JSONType: ...

    def post(self, url: str, data: JSONType) -> JSONType: ...

    def post_multipart(self, url: str, data: Dict[str, Any]) -> JSONType: ...

    def put(self, url: str, data: JSONType) -> JSONType: ...

    def patch(self, url: str, data: JSONType) -> JSONType: ...

    def delete(self, url: str) -> None: ...


@dataclass
class Credentials:
    base_url: str
    user: str
    password: str


def get_client(credentials: Credentials, session: Optional[Session] = None) -> APIClient:
    return RequestsRestClient(
        credentials=credentials
    )


class RequestsRestClient(APIClient):
    credentials: Credentials
    headers: Dict[str, str]

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        verify = not env.TESTING
        _resp = requests.post(
            url=f'{credentials.base_url}/api/common/auth/authtoken/',
            json={
                "username": credentials.user,
                "password": credentials.password
            },
            verify=verify,
            headers={
                'User-Agent': USER_AGENT
            }
        )
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        token = _resp.json()['token']
        self.headers = {
            'Authorization': f'Token {token}',
            'User-Agent': USER_AGENT
        }

    def get(self, url: str) -> JSONType:
        verify = not env.TESTING
        _resp = requests.get(url=url, headers=self.headers, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def post(self, url: str, data: JSONType) -> JSONType:
        verify = not env.TESTING
        _resp = requests.post(url=url, headers=self.headers, json=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def post_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        verify = not env.TESTING
        _resp = requests.post(url=url, headers=self.headers, files=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def put(self, url: str, data: JSONType) -> JSONType:
        verify = not env.TESTING
        _resp = requests.put(url=url, headers=self.headers, json=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def patch(self, url: str, data: JSONType) -> JSONType:
        verify = not env.TESTING
        _resp = requests.patch(url=url, headers=self.headers, json=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def delete(self, url: str) -> None:
        verify = not env.TESTING
        _resp = requests.delete(url=url, headers=self.headers, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err

    def url(self, path: str) -> str:
        url: str = f'{self.credentials.base_url}{path}'
        return url
