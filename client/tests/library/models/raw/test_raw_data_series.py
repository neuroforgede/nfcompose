# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid
from typing import Dict, Any

from compose_client.library.models.raw.data_series import RawDataSeries


class RawDataSeriesConversionTest(unittest.TestCase):

    def _test_dict(self, indexes: bool = True) -> Dict[str, Any]:
        ret = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "external_id": "test",
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "MY_NAME",
            "locked": False,
            "backend": "DYNAMIC_SQL_NO_HISTORY",
            "extra_config": {
                "auto_clean_history_after_days": -1,
                "auto_clean_meta_model_after_days": -1
            },
            "allow_extra_fields": False,
            "dimensions": "http://some.url/dimensions/",
            "float_facts": "http://some.url/floatfact/",
            "string_facts": "http://some.url/stringfact/",
            "text_facts": "http://some.url/textfact/",
            "timestamp_facts": "http://some.url/timestampfact/",
            "image_facts": "http://some.url/imagefact/",
            "file_facts": "http://some.url/filefact/",
            "json_facts": "http://some.url/jsonfact/",
            "boolean_facts": "http://some.url/booleanfact/",
            "consumers": "http://some.url/consumer/",
            "data_points": "http://some.url/datapoint/",
            "history_data_points": "http://some.url/history/datapoint/",
            "data_points_bulk": "http://some.url/bulk/datapoint/",
            "data_point_validate_external_ids": "http://some.url/bulk/check-external-ids/",
            "cube_sql": "http://some.url/cubesql/",
            "create_view": "http://some.url/createview/",
            "prune_history": "http://some.url/prune/history/",
            "prune_meta_model": "http://some.url/prune/metamodel/",
            "truncate": "http://some.url/truncate/",
            "permission_user": "http://some.url/permission/user/",
            "permission_group": "http://some.url/permission/group/",
            "data_point_structure": {
                "external_id": "required: external_id",
                "payload": {
                    "111": "optional: value for string fact with id 111 ('1111')"
                }
            }
        }

        if indexes:
            ret["indexes"] = "http://some.url/index/"
        return ret


    def _assert_same(self, _dict: Dict[str, Any], parsed: RawDataSeries, indexes: bool = True) -> None:
        self.assertEqual(parsed.url, _dict['url'])
        self.assertEqual(parsed.id, _dict['id'])
        self.assertEqual(parsed.external_id, _dict['external_id'])
        self.assertEqual(parsed.point_in_time, _dict['point_in_time'])
        self.assertEqual(parsed.last_modified_at, _dict['last_modified_at'])
        self.assertEqual(parsed.name, _dict['name'])
        self.assertEqual(parsed.locked, _dict['locked'])
        self.assertEqual(parsed.backend, _dict['backend'])
        self.assertEqual(parsed.extra_config, _dict['extra_config'])
        self.assertEqual(parsed.allow_extra_fields, _dict['allow_extra_fields'])

        self.assertEqual(parsed.dimensions, _dict['dimensions'])

        self.assertEqual(parsed.float_facts, _dict['float_facts'])
        self.assertEqual(parsed.string_facts, _dict['string_facts'])
        self.assertEqual(parsed.text_facts, _dict['text_facts'])
        self.assertEqual(parsed.timestamp_facts, _dict['timestamp_facts'])
        self.assertEqual(parsed.image_facts, _dict['image_facts'])
        self.assertEqual(parsed.file_facts, _dict['file_facts'])
        self.assertEqual(parsed.json_facts, _dict['json_facts'])
        self.assertEqual(parsed.boolean_facts, _dict['boolean_facts'])

        self.assertEqual(parsed.consumers, _dict['consumers'])
        if indexes:
            self.assertIn('indexes', _dict)
            self.assertIsNotNone(parsed.indexes)
            self.assertEqual(parsed.indexes, _dict['indexes'])
        else:
            self.assertNotIn('indexes', _dict)
            self.assertIsNone(parsed.indexes)

        self.assertEqual(parsed.data_points, _dict['data_points'])
        self.assertEqual(parsed.history_data_points, _dict['history_data_points'])
        self.assertEqual(parsed.data_points_bulk, _dict['data_points_bulk'])
        self.assertEqual(parsed.data_point_validate_external_ids, _dict['data_point_validate_external_ids'])
        self.assertEqual(parsed.cube_sql, _dict['cube_sql'])
        self.assertEqual(parsed.create_view, _dict['create_view'])

        self.assertEqual(parsed.prune_history, _dict['prune_history'])
        self.assertEqual(parsed.prune_meta_model, _dict['prune_meta_model'])
        self.assertEqual(parsed.truncate, _dict['truncate'])

        self.assertEqual(parsed.permission_user, _dict['permission_user'])
        self.assertEqual(parsed.permission_group, _dict['permission_group'])

        self.assertEqual(parsed.data_point_structure, _dict['data_point_structure'])

    def test_raw_conversion(self) -> None:
        _dict = self._test_dict()
        parsed: RawDataSeries = RawDataSeries.from_dict(_dict)  # type: ignore
        self._assert_same(_dict, parsed)

    def test_raw_conversion_no_index_endpoint(self) -> None:
        _dict = self._test_dict(indexes=False)
        parsed: RawDataSeries = RawDataSeries.from_dict(_dict)  # type: ignore
        self._assert_same(_dict, parsed, indexes=False)

    def test_extra_data_raw_conversion(self) -> None:
        _dict = self._test_dict()
        _dict['extra-key'] = 'should be ignored'
        parsed: RawDataSeries = RawDataSeries.from_dict(_dict)  # type: ignore
        self._assert_same(_dict, parsed)
