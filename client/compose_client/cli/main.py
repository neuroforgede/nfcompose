# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import click

from compose_client.cli.commands.apply import apply
from compose_client.cli.commands.diff import diff
from compose_client.cli.commands.dump import dump
from compose_client.cli.commands.push import push
from compose_client.library.utils.env import TESTING
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


if TESTING:
    import urllib3  # type: ignore

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@click.group()
def cli() -> None:
    """
    NF Compose CLI - version: 2.2.5
    """
    pass


cli.add_command(diff)  # type: ignore
cli.add_command(dump)  # type: ignore
cli.add_command(apply)  # type: ignore
cli.add_command(push)  # type: ignore



