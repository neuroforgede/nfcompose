# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from urllib import parse

from django.utils.deconstruct import deconstructible
from storages.backends.s3boto3 import S3Boto3Storage  # type: ignore
from storages.utils import setting  # type: ignore
from typing import Optional, Any, Mapping

from skipper.core.middleware import get_current_request


@deconstructible
class PrivatePublicS3Boto3Storage(S3Boto3Storage):  # type: ignore

    def url(self, name: str, parameters: Optional[Any] = None, expire: Optional[Any] = None) -> Any:
        private_url = super().url(name, parameters, expire)
        if self.custom_domain:
            return private_url

        current_request = get_current_request()

        headers: Mapping[str, str]
        if current_request is not None:
            headers = current_request.headers  # get request headers somehow
        else:
            headers = {}

        behind_proxy = 'X-Nginx-Proxy' in headers and bool(headers['X-Nginx-Proxy'])

        if not behind_proxy:
            return private_url

        if self.external_endpoint_url is not None and self.external_endpoint_url != '':
            scheme = parse.urlsplit(self.external_endpoint_url).scheme
            host = parse.urlsplit(self.external_endpoint_url).netloc
            split_url = parse.urlsplit(private_url)
            return replace_in_split_url(split_url=split_url, scheme=scheme, host=host)
        return private_url


def replace_in_split_url(split_url: parse.SplitResult, scheme: Optional[str], host: Optional[str]) -> str:
    _ret = split_url
    if scheme is not None:
        _ret = _ret._replace(scheme=scheme)
    if host is not None:
        _ret = _ret._replace(netloc=host)
    return parse.urlunsplit(_ret)
