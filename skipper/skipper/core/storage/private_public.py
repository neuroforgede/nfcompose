# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


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

        s3_url_translate_to_outside_url = setting('AWS_S3_URL_TRANSLATE_TO_OUTSIDE_URL')
        if s3_url_translate_to_outside_url is None or len(s3_url_translate_to_outside_url) == 0:

            # still support the simple replace logic if we did not define any outside host setting
            s3_outside_url = setting('AWS_S3_OUTSIDE_URL')
            s3_endpoint_url = setting('AWS_S3_ENDPOINT_URL')
            if s3_outside_url is not None:
                return private_url.replace(s3_endpoint_url, s3_outside_url, 1)

            return private_url

        for rule in s3_url_translate_to_outside_url:
            match_rule = rule.get('match', {})
            match_any = match_rule.get('any', False)
            split_url = parse.urlsplit(private_url)

            if 'X-Forwarded-Proto' in headers and 'Host' in headers:
                match_scheme = 'scheme' in match_rule and match_rule['scheme'] == headers['X-Forwarded-Proto']
                match_host = 'host' in match_rule and match_rule['host'] == headers['Host']
            else:
                # at this point only match any will work
                match_scheme = False
                match_host = False

            if match_any or (match_scheme and match_host):
                replace_rule = rule.get('replace', {})
                scheme = replace_rule.get('scheme', None)
                host = replace_rule.get('host', None)
                return replace_in_split_url(split_url=split_url, scheme=scheme, host=host)
        return private_url


def replace_in_split_url(split_url: parse.SplitResult, scheme: Optional[str], host: Optional[str]) -> str:
    _ret = split_url
    if scheme is not None:
        _ret = _ret._replace(scheme=scheme)
    if host is not None:
        _ret = _ret._replace(netloc=host)
    return parse.urlunsplit(_ret)
