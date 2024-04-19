# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import abc
import logging
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple, cast, Any, Optional, Callable

import requests
from requests import Session
from requests.exceptions import HTTPError

from compose_client.library.utils import env
from compose_client.library.utils.env import get_mock_responses
from compose_client.library.utils.types import JSONType

import functools
import datetime


USER_AGENT = 'compose_cli 2.2.6'


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

    def patch_multipart(self, url: str, data: Dict[str, Any]) -> JSONType: ...

    def delete(self, url: str) -> None: ...


@dataclass
class Credentials:
    '''Wrapper object for login data, coupled with the base-url of the target.
    
    Attributes:
        base_url: URL of the target compose endpoint. Written without trailing '/'. Example: http://skipper.local:8000
    '''
    base_url: str
    user: str
    password: str


def get_client(credentials: Credentials, session: Optional[Session] = None) -> APIClient:
    '''Returns different clients depending on environment and arguments.'''
    if env.global_data.UNIT_TESTING:
        return MockRestClient(
            credentials=credentials,
            responses=get_mock_responses()
        )
    else:
        if session is not None:
            return RequestsSessionRestClient(
                credentials=credentials,
                session=session
            )
        else:
            return RequestsRestClient(
                credentials=credentials
            )


class RequestsRestClient(APIClient):
    '''Standard client object for REST activity.

    Args:
        credentials (:obj:`Credentials`): Connection information saving address and authentication data 
    
    '''
    credentials: Credentials
    verify: bool
    _headers_cache_timestamp: Optional[datetime.datetime] = None
    _headers_cache: Dict[str, str] = None

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.verify = not env.TESTING

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers_accessor()

    def _headers_accessor(self) -> Dict[str, str]:
        if self._headers_cache_timestamp is not None and (datetime.datetime.now() - self._headers_cache_timestamp).total_seconds() < 120:
            return self._headers_cache
        
        logging.debug(f"refreshing auth token for {self.credentials.base_url}")
        _resp = requests.post(
            url=f'{self.credentials.base_url}/api/common/auth/authtoken/',
            json={
                "username": self.credentials.user,
                "password": self.credentials.password
            },
            verify=self.verify,
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
        self._headers_cache = {
            'Authorization': f'Token {token}',
            'User-Agent': USER_AGENT
        }
        self._headers_cache_timestamp = datetime.datetime.now()
        return self._headers_cache

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

    def patch_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        verify = not env.TESTING
        _resp = requests.patch(url=url, headers=self.headers, files=data, verify=verify)
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


class RequestsRestLoggingClient(RequestsRestClient):
    ''' Extension of RequestsRestClient with added logging. Do not use for production due to possible memory bloat.

    For every REST method there exists a log 'log_<method>_requests', which is a chronological list of requests. See
    attributes section.

    Attributes:
        log_get_requests: List of urls
        log_delete_requests: List of urls
        log_post_requests: List of Tuples (target url, request content)
        log_post_multipart_requests: List of Tuples (target url, request content)
        log_put_requests: List of Tuples (target url, request content)
        log_patch_requests: List of Tuples (target url, request content)
        log_patch_multipart_requests: List of Tuples (target url, request content)
    '''
    log_get_requests: List[str] = []
    log_delete_requests: List[str] = []
    log_post_requests: List[Tuple[str, JSONType]] = []
    log_post_multipart_requests: List[Tuple[str, Dict[str, Any]]] = []
    log_put_requests: List[Tuple[str, JSONType]] = []
    log_patch_requests: List[Tuple[str, JSONType]] = []
    log_patch_multipart_requests: List[Tuple[str, Dict[str, Any]]] = []

    def clear_log(self) -> None:
        self.log_get_requests = []
        self.log_delete_requests = []
        self.log_post_requests = []
        self.log_post_multipart_requests = []
        self.log_put_requests = []
        self.log_patch_requests = []
        self.log_patch_multipart_requests = []

    def get(self, url: str) -> JSONType:
        self.log_get_requests.append(url)
        return super().get(url)

    def post(self, url: str, data: JSONType) -> JSONType:
        self.log_post_requests.append((url, data))
        return super().post(url, data)

    def delete(self, url: str) -> None:
        self.log_delete_requests.append(url)
        return super().delete(url)

    def put(self, url: str, data: JSONType) -> JSONType:
        self.log_put_requests.append((url, data))
        return super().put(url, data)

    def patch(self, url: str, data: JSONType) -> JSONType:
        self.log_patch_requests.append((url, data))
        return super().patch(url, data)

    def post_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        self.log_post_multipart_requests.append((url, data))
        return super().post_multipart(url, data)

    def patch_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        self.log_patch_multipart_requests.append((url, data))
        return super().patch_multipart(url, data)


class FeatureHidingClient(RequestsRestLoggingClient):
    '''Intercepts get-responses and removes any of the specified keys.

    Will work differently for paginated results, applies to every content element instead.

    Args:
        hidden_rest_features(List[str]): List of Keys that shall be removed from every GET response.
    '''
    hidden_rest_features: List[str]

    def __init__(self, hidden_rest_features: List[str], credentials: Credentials):
        self.hidden_rest_features = hidden_rest_features
        super().__init__(credentials)

    def get(self, url: str) -> JSONType:
        ret = super().get(url)

        def remove_features(obj: JSONType) -> None:
            if isinstance(obj, dict):
                for feature in self.hidden_rest_features:
                    if feature in obj:
                        obj.pop(feature)

        if isinstance(ret, list):
            for obj in ret:
                    remove_features(obj)
        elif isinstance(ret, dict):
            if set(['count', 'next', 'results']).issubset(ret.keys()):
                for result in ret['results']:
                    remove_features(result)
            else:
                remove_features(ret)

        return ret


class RequestsSessionRestClient(APIClient):
    session: Session
    credentials: Credentials
    verify: bool
    _headers_cache_timestamp: Optional[datetime.datetime] = None
    _headers_cache: Dict[str, str] = None

    def __init__(self, session: Session, credentials: Credentials):
        self.credentials = credentials
        self.session = session
        self.verify = not env.TESTING

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers_accessor()

    def _headers_accessor(self) -> Dict[str, str]:
        if self._headers_cache_timestamp is not None and (datetime.datetime.now() - self._headers_cache_timestamp).total_seconds() < 120:
            return self._headers_cache
        
        logging.debug(f"refreshing auth token for {self.credentials.base_url}")
        _resp = self.session.post(
            url=f'{self.credentials.base_url}/api/common/auth/authtoken/',
            json={
                "username": self.credentials.user,
                "password": self.credentials.password
            },
            headers={
                'User-Agent': USER_AGENT
            },
            verify=self.verify
        )
        try: 
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        token = _resp.json()['token']
        self._headers_cache = {
            'Authorization': f'Token {token}',
            'User-Agent': USER_AGENT
        }
        self._headers_cache_timestamp = datetime.datetime.now()
        return self._headers_cache

    def get(self, url: str) -> JSONType:
        verify = not env.TESTING
        _resp = self.session.get(url=url, headers=self.headers, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def post(self, url: str, data: JSONType) -> JSONType:
        verify = not env.TESTING
        _resp = self.session.post(url=url, headers=self.headers, json=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def post_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        verify = not env.TESTING
        _resp = self.session.post(url=url, headers=self.headers, files=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def put(self, url: str, data: JSONType) -> JSONType:
        verify = not env.TESTING
        _resp = self.session.put(url=url, headers=self.headers, json=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def patch_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        verify = not env.TESTING
        _resp = self.session.patch(url=url, headers=self.headers, files=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())
    
    def patch(self, url: str, data: JSONType) -> JSONType:
        verify = not env.TESTING
        _resp = self.session.patch(url=url, headers=self.headers, json=data, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err
        return cast(JSONType, _resp.json())

    def delete(self, url: str) -> None:
        verify = not env.TESTING
        _resp = self.session.delete(url=url, headers=self.headers, verify=verify)
        try:
            _resp.raise_for_status()
        except HTTPError as http_err:
            print(_resp.content, file=sys.stderr)
            raise http_err

    def url(self, path: str) -> str:
        url: str = f'{self.credentials.base_url}{path}'
        return url


HTTP_METHOD = str


class MockRestClient(APIClient):
    ''' Answers REST Requests with content that was predefined in the constructor.
    
    Args:
        credentials (:obj:`Credentials`): Connection information saving address and authentication data.
        responses (:obj:`Dict`): Predefined mock responses.

    Example:
        test_client = MockRestClient(test_credentials, {
            "user": {
                "get": {
                    f'http://some.mock.url/test_path/': {
                        "next": f'http://some.mock.url/test_path1',
                        "results": [
                            {
                                "external_id": "1"
                            }
                        ]
                    }
                }
            }
        })
    '''
    responses: Dict[HTTP_METHOD, Dict[str, JSONType]]
    credentials: Credentials

    def __init__(self, credentials: Credentials, responses: Dict[HTTP_METHOD, Dict[str, JSONType]]):
        self.responses = responses[credentials.user]
        self.credentials = credentials

    def get(self, url: str) -> JSONType:
        return cast(JSONType, self.responses['get'][url])

    def url(self, path: str) -> str:
        url: str = f'{self.credentials.base_url}{path}'
        return url

    def post(self, url: str, data: JSONType) -> JSONType:
        return cast(JSONType, self.responses['post'][url])

    def post_multipart(self, url: str, data: Dict[str, Any]) -> JSONType:
        return cast(JSONType, self.responses['post'][url])

    def put(self, url: str, data: JSONType) -> JSONType:
        return cast(JSONType, self.responses['put'][url])

    def patch(self, url: str, data: JSONType) -> JSONType:
        raise NotImplementedError()

    def delete(self, url: str) -> None:
        pass
