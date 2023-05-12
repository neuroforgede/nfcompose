# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
import errno
import hashlib
import json
import os
import re
import sys
from typing import Any, Type, Optional, Iterable, Dict, Mapping, Callable, List
from urllib.parse import urlparse

import click
import requests
from requests import HTTPError

from compose_client.library.connection.client import Credentials, get_client, USER_AGENT
from compose_client.library.models.definition.datapoint import FileTypeContent
from compose_client.library.models.domain_aliases import parse_domain_aliases, invert_dict
from compose_client.library.service.fetcher import ComposeDataSeriesDefinitionFetcher, ComposeEngineDefinitionFetcher, \
    Fetcher, \
    URL, ComposeGroupDefinitionFetcher, ComposeDataPointFetcher, ComposeHttpEndpointDefinitionFetcher
from compose_client.library.storage.file import LocalFileStorageAdapter, EnumEncoder
from compose_client.library.utils.types import JSONType


@click.group()
def dump() -> None:
    """
    Dump structural definitions and/or data to a target file or stdout
    """
    pass


def _dump(
        outfile: str,
        fetcher: Fetcher[URL, Any],
        kwargs: Dict[str, Any],
        encoder: Type[json.JSONEncoder] = EnumEncoder,
        order_by: Optional[Callable[[Any], Any]] = None
) -> None:
    definitions = fetcher.fetch(**kwargs)

    _defs_as_dicts = list(map(lambda x: x.to_dict(), definitions))  # type: ignore

    if order_by is not None:
        _defs_as_dicts = list(sorted(_defs_as_dicts, key=order_by))  # type: ignore

    if outfile is not None and outfile != '':
        storage_adapter = LocalFileStorageAdapter(encoder)
        storage_adapter.write_json(outfile, data=_defs_as_dicts)
    else:
        print(json.dumps(_defs_as_dicts, cls=encoder, indent=4))


def _dump_lines(
        outfile: str,
        fetcher: Fetcher[URL, Any],
        kwargs: Dict[str, Any],
        encoder: Type[json.JSONEncoder] = EnumEncoder
) -> None:

    def _dict_gen() -> Iterable[Dict[str, Any]]:
        definitions = fetcher.fetch(**kwargs)
        for _def in definitions:
            as_dict = _def.to_dict()
            yield as_dict

    if outfile is not None and outfile != '':
        storage_adapter = LocalFileStorageAdapter(encoder)
        storage_adapter.write_json_lines(outfile, data=_dict_gen())
    else:
        for _dict in _dict_gen():
            print(json.dumps(_dict, cls=encoder), file=sys.stdout)


@dump.command('dataseries')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option('--domain-aliases', type=click.STRING, required=False, help='JSON Mapping of domains and ports')
@click.option('--regex-filter', type=click.STRING, required=False, help='regex filter to filter the dataseries to include/exclude based on their external_id')
@click.option('--external-id', type=click.STRING, required=False, multiple=True, help='only include dataseries with this external_id')
@click.option('--outfile', type=click.STRING,
              help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.argument('src')
def dump_data_series_definitions(
        src: str,
        outfile: str,
        compose_user: str,
        compose_password: str,
        domain_aliases: Optional[str],
        regex_filter: Optional[str],
        external_id: List[str]
) -> None:
    """
    Dumps DataSeries Definitions
    """

    domain_aliases_obj = parse_domain_aliases(domain_aliases)
    inverted_domain_aliases_obj = invert_dict(domain_aliases_obj)
    if inverted_domain_aliases_obj is None:
        raise AssertionError('passed domain aliases are not invertible')

    _dump(
        outfile=outfile,
        fetcher=ComposeDataSeriesDefinitionFetcher(
            client=get_client(
                credentials=Credentials(
                    base_url=src,
                    user=compose_user,
                    password=compose_password
                )
            )
        ),
        kwargs={
            "domain_aliases": inverted_domain_aliases_obj,
            "regex_filter": regex_filter,
            "external_ids": external_id
        },
        order_by=lambda x: x['data_series']['external_id']
    )


@dump.command('engines')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option('--domain-aliases', type=click.STRING, required=False, help='JSON Mapping of domains and ports')
@click.option('--outfile', type=click.STRING,
              help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.argument('src')
def dump_engine_definitions(
        src: str,
        outfile: str,
        compose_user: str,
        compose_password: str,
        domain_aliases: Optional[str]
) -> None:
    """
    Dumps Engine Definitions
    """

    domain_aliases_obj = parse_domain_aliases(domain_aliases)
    inverted_domain_aliases_obj = invert_dict(domain_aliases_obj)
    if inverted_domain_aliases_obj is None:
        raise AssertionError('passed domain aliases are not invertible')

    _dump(
        outfile=outfile,
        fetcher=ComposeEngineDefinitionFetcher(
            client=get_client(
                credentials=Credentials(
                    base_url=src,
                    user=compose_user,
                    password=compose_password
                )
            )
        ),
        kwargs={"domain_aliases": inverted_domain_aliases_obj},
        order_by=lambda x: x['engine']['external_id']
    )


@dump.command('httpendpoints')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option('--outfile', type=click.STRING,
              help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.argument('src')
def dump_http_endpoint_definitions(
        src: str,
        outfile: str,
        compose_user: str,
        compose_password: str
) -> None:
    """
    Dumps HttpEndpoint Definitions
    """
    _dump(
        outfile=outfile,
        fetcher=ComposeHttpEndpointDefinitionFetcher(
            client=get_client(
                credentials=Credentials(
                    base_url=src,
                    user=compose_user,
                    password=compose_password
                )
            )
        ),
        kwargs={},
        order_by=lambda x: x['http_endpoint']['external_id']
    )


@dump.command('groups')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option('--outfile', type=click.STRING,
              help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.argument('src')
def dump_group_definitions(
        src: str,
        outfile: str,
        compose_user: str,
        compose_password: str
) -> None:
    """
    Dumps Group Definitions
    """
    _dump(
        outfile=outfile,
        fetcher=ComposeGroupDefinitionFetcher(
            client=get_client(
                credentials=Credentials(
                    base_url=src,
                    user=compose_user,
                    password=compose_password
                )
            )
        ),
        kwargs={},
        order_by=lambda x: x['group']['name']
    )


@dump.command('datapoints')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option('--extra-file-dir', type=click.STRING)
@click.option('--outfile', type=click.STRING,
              help='if set, the output will be written into this file, otherwise, output will be written to stdout')
@click.option('--lines', type=click.BOOL, required=False, is_flag=True, help='whether to output the data in jsonlines format')
@click.option('--filter', type=click.STRING, required=False, help='json filter for the payload')
@click.option(
    '--changes-since',
    type=click.DateTime(
        formats=['%Y-%m-%dT%H:%M:%S.%f']
    ),
    required=False,
    help='only include datapoints that were changed since this datetime'
)
@click.option('--external-id', type=click.STRING, required=False, multiple=True, help='only include datapoints with these external ids')
@click.option('--pagesize', type=click.INT, default=100)
@click.argument('src')
@click.argument('data_series_external_id')
def dump_datapoints(
        src: str,
        data_series_external_id: str,
        outfile: str,
        extra_file_dir: Optional[str],
        compose_user: str,
        compose_password: str,
        lines: bool,
        pagesize: int,
        filter: Optional[str],
        external_id: Optional[List[str]],
        changes_since: Optional[datetime.datetime]
) -> None:
    """
    Dumps DataPoints
    """

    _external_id = external_id
    if not _external_id:
        # no external id passed, dont filter
        # empty lists/iterables cause the fetcher to return
        # and empty list
        _external_id = None

    filter_json: Optional[JSONType] = None
    if filter is not None:
        filter_json = json.loads(filter)

    class DataPointEncoder(EnumEncoder):
        def default(self, obj: Any) -> Any:
            if isinstance(obj, FileTypeContent):
                if extra_file_dir is None or extra_file_dir == '':
                    raise click.ClickException('--extra-file-dir is required for dataseries that have file-shaped data in it')
                with requests.get(obj.url, headers={
                    'User-Agent': USER_AGENT
                }) as response:
                    try:
                        response.raise_for_status()
                    except HTTPError as http_err:
                        print(response.content, file=sys.stderr)
                        raise http_err

                    fname: str
                    if "Content-Disposition" in response.headers.keys():
                        fname = re.findall("filename=(.+)", response.headers["Content-Disposition"])[0]
                    else:
                        fname = urlparse(obj.url).path

                    _hashed_fname = hashlib.sha256(fname.encode('UTF-8')).hexdigest()

                    final_name = f'{extra_file_dir}/{_hashed_fname}'

                    _dir = os.path.dirname(final_name)
                    if _dir != '':
                        if not os.path.exists(os.path.dirname(final_name)):
                            try:
                                os.makedirs(os.path.dirname(final_name))
                            except OSError as exc:  # Guard against race condition
                                if exc.errno != errno.EEXIST:
                                    raise

                    with open(final_name, 'wb') as file:
                        file.write(response.content)

                    return final_name
            return EnumEncoder.default(self, obj)

    filter_obj: Optional[Dict[str, Any]] = None
    if filter is not None and filter != '':
        filter_obj = json.loads(filter)

    session = requests.Session()
    try:
        if lines:
            _dump_lines(
                outfile=outfile,
                fetcher=ComposeDataPointFetcher(
                    client=get_client(
                        credentials=Credentials(
                            base_url=src,
                            user=compose_user,
                            password=compose_password
                        ),
                        session=session
                    ),
                    data_series_external_id=data_series_external_id,
                    pagesize=pagesize,
                    filter=filter_obj,
                    external_ids=_external_id,
                    changes_since=changes_since
                ),
                encoder=DataPointEncoder,
                kwargs={}
            )
        else:
            _dump(
                outfile=outfile,
                fetcher=ComposeDataPointFetcher(
                    client=get_client(
                        credentials=Credentials(
                            base_url=src,
                            user=compose_user,
                            password=compose_password
                        ),
                        session=session
                    ),
                    data_series_external_id=data_series_external_id,
                    pagesize=pagesize,
                    filter=filter_obj,
                    external_ids=_external_id,
                    changes_since=changes_since
                ),
                encoder=DataPointEncoder,
                kwargs={},
                # the regular json format is intended to be committed into source control,
                # so we need to ensure order so diff tools behaves nicely
                order_by=lambda x: x['external_id']
            )
    finally:
        session.close()
