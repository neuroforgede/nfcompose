# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import json
import unittest

from click.testing import CliRunner

from compose_client.cli.main import cli
from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition
from compose_client.library.utils import env
from compose_client.library.utils.env import set_mock_responses
from tests.cli.commands.fake import fake_data_series_gets

fake_compose_url_1 = 'http://some.mock.url'


class CLIDumpTest(unittest.TestCase):

    def test_dump_data_series_remote(self) -> None:
        env.global_data.UNIT_TESTING = True
        ds_1_id = '09a1d5ef-6dea-45d5-9743-3d88499345fe'
        ds_2_id = '09a1d5ef-6dea-45d5-9743-3d88499345ff'
        set_mock_responses({
            'user1': {
                'get': {
                    **fake_data_series_gets(fake_compose_url_1, ds_1_id, 'my_ds', ds_2_id, 'my_ds_2')
                }
            }
        })

        runner = CliRunner(mix_stderr=True)
        result = runner.invoke(cli, [
            'dump',
            'dataseries',
            '--compose-user', 'user1',
            '--compose-password', 'pw1',
            fake_compose_url_1
        ])

        self.assertEqual(0, result.exit_code)

        out_as_json = json.loads(result.stdout)

        self.assertIsInstance(out_as_json, list)

        # check if we got a dump executed and we can parse a dump from the result
        definition = DataSeriesDefinition.from_dict(out_as_json[0])

        self.assertEqual('my_ds', definition.data_series.external_id)