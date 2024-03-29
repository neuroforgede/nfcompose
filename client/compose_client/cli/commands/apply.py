# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import json
import sys

import click

from compose_client.library.connection.client import RequestsRestClient, Credentials
from compose_client.library.models.diff.data_series import DataSeriesDefinitionDiff
from compose_client.library.models.diff.engine import EngineDefinitionDiff
from compose_client.library.models.diff.group import GroupDefinitionDiff
from compose_client.library.models.diff.http_endpoint import HttpEndpointDefinitionDiff
from compose_client.library.models.operation.create_data_series_view import DataSeriesCreateViewOperation
from compose_client.library.service.pusher import DataSeriesDefinitionDiffPusher, EngineDefinitionDiffPusher, \
    DataSeriesCreateViewOperationPusher, GroupDefinitionDiffPusher, HttpEndpointDefinitionDiffPusher
from compose_client.library.storage.file import LocalFileStorageAdapter


@click.group()
def apply() -> None:
    """
    Apply structural changes to a NF Compose installation
    """
    pass


@apply.command('dataseries-diff')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option(
    '--file',
    type=click.STRING,
    required=sys.stdin.isatty(),
    help='the file to read the diff from, (only required if running in a tty)'
)
@click.option('-v', '--verbose', count=True)
@click.argument('target')
def apply_data_series_definition_diff(
        file: str,
        target: str,
        compose_user: str,
        compose_password: str,
        verbose: int
) -> None:
    """
    apply diff of dataseries
    """
    if file is not None and file != '':
        storage_adapter = LocalFileStorageAdapter()
        data = storage_adapter.read_json(file)
    else:
        data = json.load(sys.stdin)

    _diffs = list(map(DataSeriesDefinitionDiff.from_dict, data))

    if verbose > 0:
        print(f'applying diffs to {len(_diffs)} dataseries as user {compose_user} on {target}')
    if verbose > 1:
        print(f'diffs: {json.dumps(data, indent=4)}')

    pusher = DataSeriesDefinitionDiffPusher(client=RequestsRestClient(
        credentials=Credentials(
            base_url=target,
            user=compose_user,
            password=compose_password
        )
    ))

    pusher.push(data=_diffs)


@apply.command('engines-diff')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option(
    '--file',
    type=click.STRING,
    required=sys.stdin.isatty(),
    help='the file to read the diff from, (only required if running in a tty)'
)
@click.option('-v', '--verbose', count=True)
@click.argument('target')
def apply_engines_definition_diff(
        file: str,
        target: str,
        compose_user: str,
        compose_password: str,
        verbose: int
) -> None:
    """
    apply diff of engines
    """
    if file is not None and file != '':
        storage_adapter = LocalFileStorageAdapter()
        data = storage_adapter.read_json(file)
    else:
        data = json.load(sys.stdin)

    _diffs = list(map(EngineDefinitionDiff.from_dict, data))

    if verbose > 0:
        print(f'applying diffs to {len(_diffs)} engines as user {compose_user} on {target}')
    if verbose > 1:
        print(f'diffs: {json.dumps(data, indent=4)}')

    pusher = EngineDefinitionDiffPusher(client=RequestsRestClient(
        credentials=Credentials(
            base_url=target,
            user=compose_user,
            password=compose_password
        )
    ))

    pusher.push(data=_diffs)


@apply.command('httpendpoints-diff')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option(
    '--file',
    type=click.STRING,
    required=sys.stdin.isatty(),
    help='the file to read the diff from, (only required if running in a tty)'
)
@click.option('-v', '--verbose', count=True)
@click.argument('target')
def apply_httpendpoints_definition_diff(
        file: str,
        target: str,
        compose_user: str,
        compose_password: str,
        verbose: int
) -> None:
    """
    apply diff of httpendpoints
    """
    if file is not None and file != '':
        storage_adapter = LocalFileStorageAdapter()
        data = storage_adapter.read_json(file)
    else:
        data = json.load(sys.stdin)

    _diffs = list(map(HttpEndpointDefinitionDiff.from_dict, data))

    if verbose > 0:
        print(f'applying diffs to {len(_diffs)} httpendpoints as user {compose_user} on {target}')
    if verbose > 1:
        print(f'diffs: {json.dumps(data, indent=4)}')

    pusher = HttpEndpointDefinitionDiffPusher(client=RequestsRestClient(
        credentials=Credentials(
            base_url=target,
            user=compose_user,
            password=compose_password
        )
    ))

    pusher.push(data=_diffs)


@apply.command('groups-diff')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option(
    '--file',
    type=click.STRING,
    required=sys.stdin.isatty(),
    help='the file to read the diff from, (only required if running in a tty)'
)
@click.option('-v', '--verbose', count=True)
@click.argument('target')
def apply_groups_definition_diff(
        file: str,
        target: str,
        compose_user: str,
        compose_password: str,
        verbose: int
) -> None:
    """
    apply diff of groups
    """
    if file is not None and file != '':
        storage_adapter = LocalFileStorageAdapter()
        data = storage_adapter.read_json(file)
    else:
        data = json.load(sys.stdin)

    _diffs = list(map(GroupDefinitionDiff.from_dict, data))

    if verbose > 0:
        print(f'applying diffs to {len(_diffs)} groups as user {compose_user} on {target}')
    if verbose > 1:
        print(f'diffs: {json.dumps(data, indent=4)}')

    pusher = GroupDefinitionDiffPusher(client=RequestsRestClient(
        credentials=Credentials(
            base_url=target,
            user=compose_user,
            password=compose_password
        )
    ))

    pusher.push(data=_diffs)


@apply.command('dataseries-create-view')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option(
    '--file',
    type=click.STRING,
    required=sys.stdin.isatty(),
    help='the file to read the diff from, (only required if running in a tty)'
)
@click.option('-v', '--verbose', count=True)
@click.argument('target')
def apply_data_series_create_view(
        file: str,
        target: str,
        compose_user: str,
        compose_password: str,
        verbose: int
) -> None:
    """
    apply a set of dataseries-create-view operations
    """
    if file is not None and file != '':
        storage_adapter = LocalFileStorageAdapter()
        data = storage_adapter.read_json(file)
    else:
        data = json.load(sys.stdin)

    _diffs = list(map(DataSeriesCreateViewOperation.from_dict, data))

    if verbose > 0:
        print(f'applying {len(_diffs)} dataseries-create-view operations as user {compose_user} on {target}')
    if verbose > 1:
        print(f'diffs: {json.dumps(data, indent=4)}')

    pusher = DataSeriesCreateViewOperationPusher(client=RequestsRestClient(
        credentials=Credentials(
            base_url=target,
            user=compose_user,
            password=compose_password
        )
    ))

    pusher.push(data=_diffs)
