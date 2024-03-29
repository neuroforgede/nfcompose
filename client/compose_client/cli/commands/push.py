# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import json
import sys
from typing import Iterable

import click

from compose_client.library.connection.client import RequestsRestClient, Credentials
from compose_client.library.models.definition.datapoint import DataPoint
from compose_client.library.service.pusher import DataPointPusher
from compose_client.library.storage.file import LocalFileStorageAdapter, read_json_lines_from_stream


@click.group()
def push() -> None:
    """
    Pushes non-structural data such as DataPoints to a NF Compose installation
    """
    pass


@push.command('datapoints')  # type: ignore
@click.option('--compose-user', type=click.STRING, required=True)
@click.option('--compose-password', type=click.STRING, required=True)
@click.option('--lines', type=click.BOOL, required=False, is_flag=True, help='whether to interpret the input as being in jsonlines format')
@click.option('--asynchronous', '--async', type=click.BOOL, required=False, is_flag=True, help='whether to instruct NF Compose to store the data asynchronously')
@click.option('--batchsize', type=click.INT, default=100)
@click.option(
    '--file',
    type=click.STRING,
    required=sys.stdin.isatty(),
    help='the file to read the datapoints from, (only required if running in a tty)'
)
@click.argument('target')
@click.argument('data_series_external_id')
def push_datapoint_definitions(
        file: str,
        target: str,
        data_series_external_id: str,
        compose_user: str,
        compose_password: str,
        lines: bool,
        asynchronous: bool,
        batchsize: int
) -> None:
    """
    Pushes DataPoints to a Compose instance
    """

    _dps: Iterable[DataPoint]

    if lines:
        if file is not None and file != '':
            storage_adapter = LocalFileStorageAdapter()
            data_as_json = storage_adapter.read_json_lines(file)
        else:
            data_as_json = read_json_lines_from_stream(sys.stdin)
    else:
        if file is not None and file != '':
            storage_adapter = LocalFileStorageAdapter()
            data_as_json = storage_adapter.read_json(file)
        else:
            data_as_json = json.load(sys.stdin)

    # explicitly dont convert to list here or we lose the streaming capabilities
    _dps = map(DataPoint.from_dict, data_as_json)

    pusher = DataPointPusher(
        client=RequestsRestClient(
            credentials=Credentials(
                base_url=target,
                user=compose_user,
                password=compose_password
            )
        ),
        batch_size=batchsize
    )
    pusher.push(_dps, data_series_external_id=data_series_external_id, asynchronous=asynchronous)
