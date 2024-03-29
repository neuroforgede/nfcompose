# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import json
import unittest

from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Patcher  # type: ignore

from compose_client.cli.main import cli
from compose_client.library.models.diff.data_series import DataSeriesDefinitionDiff
from compose_client.library.utils import env
from compose_client.library.utils.env import set_mock_responses
from tests.cli.commands.fake import fake_data_series_gets

dump_1 = """
[
    {
        "data_series": {
            "allow_extra_fields": false,
            "backend": "DYNAMIC_SQL_MATERIALIZED",
            "external_id": "my_little_pony",
            "extra_config": {
                "auto_clean_history_after_days": -1,
                "auto_clean_meta_model_after_days": -1
            },
            "name": "my_little_pony"
        },
        "structure": {
            "boolean_facts": [],
            "file_facts": [],
            "float_facts": [
                {
                    "external_id": "sssasdfsafsa",
                    "name": "sdfsfsfafd",
                    "optional": false
                }
            ],
            "image_facts": [
                {
                    "external_id": "sss",
                    "name": "ssss",
                    "optional": false
                }
            ],
            "json_facts": [],
            "string_facts": [],
            "text_facts": [],
            "timestamp_facts": [],
            "dimensions": [
                {
                    "external_id": "my_dim",
                    "name": "my_dim",
                    "optional": false,
                    "reference": "my_little_pony"
                }
            ]
        }
    }
]
"""

dump_2 = """
[
    {
        "data_series": {
            "allow_extra_fields": false,
            "backend": "DYNAMIC_SQL_MATERIALIZED",
            "external_id": "my_little_pony",
            "extra_config": {
                "auto_clean_history_after_days": -1,
                "auto_clean_meta_model_after_days": -1
            },
            "name": "my_little_pony"
        },
        "structure": {
            "boolean_facts": [],
            "file_facts": [],
            "float_facts": [],
            "image_facts": [
                {
                    "external_id": "sss",
                    "name": "ssss",
                    "optional": false
                }
            ],
            "json_facts": [],
            "string_facts": [],
            "text_facts": [],
            "timestamp_facts": [],
            "dimensions": []
        }
    }
]
"""

fake_compose_url_1 = 'http://some.mock.url'
fake_compose_url_2 = 'http://some.other.mock.url'


class CLIDiffTest(unittest.TestCase):

    def test_diff_data_series_files(self) -> None:
        runner = CliRunner()
        with Patcher() as patcher:
            patcher.fs.create_file('dump1.json', contents=dump_1)
            patcher.fs.create_file('dump2.json', contents=dump_2)

            result = runner.invoke(cli, ['diff', 'dataseries', 'dump1.json', 'dump2.json'])

            self.assertEqual(0, result.exit_code)

            out_as_json = json.loads(result.stdout)

            self.assertIsInstance(out_as_json, list)
            # check if we got a diff executed and we can parse a diff from the result
            diff = DataSeriesDefinitionDiff.from_dict(out_as_json[0])

            self.assertEqual(1, len(diff.structure.float_facts))

    def test_diff_data_series_remote(self) -> None:
        env.global_data.UNIT_TESTING = True
        ds_1_id = '09a1d5ef-6dea-45d5-9743-3d88499345fe'
        ds_2_id = '09a1d5ef-6dea-45d5-9743-3d88499345ff'
        set_mock_responses({
            'user1': {
                'get': {
                    **fake_data_series_gets(fake_compose_url_1, ds_1_id, 'my_ds', ds_2_id, 'my_ds_2')
                }
            },
            'user2': {
                'get': {
                    f'{fake_compose_url_2}/api/dataseries/dataseries/': {
                        "count": 0,
                        "next": None,
                        "previous": None,
                        "results": []
                    }
                }
            }
        })

        runner = CliRunner(mix_stderr=True)
        result = runner.invoke(cli, [
            'diff',
            'dataseries',
            '--base-type', 'compose',
            '--base-compose-user', 'user2',
            '--base-compose-password', 'pw2',
            '--target-type', 'compose',
            '--target-compose-user', 'user1',
            '--target-compose-password', 'pw1',
            fake_compose_url_2,
            fake_compose_url_1
        ])

        self.assertEqual(0, result.exit_code)

        out_as_json = json.loads(result.stdout)

        self.assertIsInstance(out_as_json, list)

        self.assertEqual(2, len(out_as_json))

        _diffs = set([DataSeriesDefinitionDiff.from_dict(elem).external_id for elem in out_as_json])

        self.assertIn('my_ds', _diffs)
        self.assertIn('my_ds_2', _diffs)


