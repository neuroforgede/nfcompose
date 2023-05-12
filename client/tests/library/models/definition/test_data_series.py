# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid

from compose_client.library.models.definition.data_series import DataSeries
from compose_client.library.models.raw.data_series import RawDataSeries


class FactConversionTest(unittest.TestCase):

    def test_conversion(self) -> None:
        raw = RawDataSeries(
            url="http://some.url/",
            id=str(uuid.uuid4()),
            external_id="test",
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name="MY_NAME",
            locked=False,
            backend="DYNAMIC_SQL_NO_HISTORY",
            extra_config={
                "auto_clean_history_after_days": -1,
                "auto_clean_meta_model_after_days": -1
            },
            allow_extra_fields=False,
            dimensions="http://some.url/dimensions/",
            float_facts="http://some.url/floatfact/",
            string_facts="http://some.url/stringfact/",
            text_facts="http://some.url/textfact/",
            timestamp_facts="http://some.url/timestampfact/",
            image_facts="http://some.url/imagefact/",
            file_facts="http://some.url/filefact/",
            json_facts="http://some.url/jsonfact/",
            boolean_facts="http://some.url/booleanfact/",
            consumers="http://some.url/consumer/",
            data_points="http://some.url/datapoint/",
            history_data_points="http://some.url/history/datapoint/",
            data_points_bulk="http://some.url/bulk/datapoint/",
            data_point_validate_external_ids="http://some.url/bulk/check-external-ids/",
            cube_sql="http://some.url/cubesql/",
            create_view="http://some.url/createview/",
            prune_history="http://some.url/prune/history/",
            prune_meta_model="http://some.url/prune/metamodel/",
            truncate="http://some.url/truncate/",
            permission_user="http://some.url/permission/user/",
            permission_group="http://some.url/permission/group/",
            data_point_structure={
                "external_id": "required: external_id",
                "payload": {
                    "111": "optional: value for string fact with id 111 ('1111')"
                }
            }
        )
        parsed = DataSeries.from_raw(raw)

        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.allow_extra_fields, raw.allow_extra_fields)
        self.assertEqual(parsed.backend, raw.backend)

        self.assertEqual(parsed.extra_config, raw.extra_config)
        # should be a copy and not the same object
        self.assertNotEqual(id(parsed.extra_config), id(raw.extra_config))
