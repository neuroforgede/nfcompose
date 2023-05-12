# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest

from compose_client.library.models.definition.consumer import Consumer
from compose_client.library.models.definition.data_series import DataSeries
from compose_client.library.models.definition.data_series_definition import DataSeriesStructure, DataSeriesDefinition
from compose_client.library.models.definition.dimension import Dimension
from compose_client.library.models.definition.index import Index, IndexTarget
from compose_client.library.models.definition.facts import FloatFact, BooleanFact, JsonFact, FileFact, ImageFact, TimestampFact, \
    TextFact, \
    StringFact
from compose_client.library.service.diff import diff_data_series
from compose_client.library.models.operation.general import OperationType


class DataSeriesDefinitionDiffTest(unittest.TestCase):
    """
    tests properly generating the difference between two DataSeriesDefinitions
    As of now, this mostly checks if the data is routed to the proper methods
    and diffs show up in the correct output property since it is expected
    to have all the internally used diff checks properly tested somewhere else
    """
    def gen_all_set(self) -> DataSeriesDefinition:
        return DataSeriesDefinition(
            consumers=[Consumer(
                external_id='consumer',
                target='http://my.nodered.local/',
                name='consumer',
                headers={},
                timeout=10,
                retry_backoff_every=1,
                retry_backoff_delay="00:00:30",
                retry_max=1
            )],
            data_series=DataSeries(
                external_id='my_ds',
                name='my_ds',
                backend='DYNAMIC_SQL',
                extra_config={
                    "auto_clean_history_after_days": -1,
                    "auto_clean_meta_model_after_days": -1
                },
                allow_extra_fields=True
            ),
            indexes=[Index(
                external_id='index',
                name='index',
                targets=[
                    IndexTarget(
                        target_external_id='image',
                        target_type='IMAGE_FACT'
                    ),
                    IndexTarget(
                        target_external_id='boolean',
                        target_type='BOOLEAN_FACT'
                    )
                ]
            )],
            structure=DataSeriesStructure(
                float_facts=[FloatFact(
                    external_id='float',
                    name='float',
                    optional=False
                )],
                string_facts=[StringFact(
                    external_id='string',
                    name='string',
                    optional=False
                )],
                text_facts=[TextFact(
                    external_id='text',
                    name='text',
                    optional=False
                )],
                timestamp_facts=[TimestampFact(
                    external_id='timestamp',
                    name='timestamp',
                    optional=False
                )],
                image_facts=[ImageFact(
                    external_id='image',
                    name='image',
                    optional=False
                )],
                file_facts=[FileFact(
                    external_id='file',
                    name='file',
                    optional=False
                )],
                json_facts=[JsonFact(
                    external_id='json',
                    name='json',
                    optional=False
                )],
                boolean_facts=[BooleanFact(
                    external_id='boolean',
                    name='boolean',
                    optional=False
                )],
                dimensions=[Dimension(
                    external_id='dimension',
                    name='dimension',
                    optional=False,
                    reference='some_other_ds'
                )]
            )
        )

    def test_new_data_series(self) -> None:
        base = None
        target = self.gen_all_set()

        diff = diff_data_series(base, target)
        self.assertIsNotNone(diff.data_series)
        self.assertEqual(OperationType.CREATE, diff.data_series.operation_type)
        self.assertEqual(target.data_series.to_dict(), diff.data_series.payload)
        self.assertEqual(1, len(diff.structure.float_facts))
        self.assertEqual(1, len(diff.structure.string_facts))
        self.assertEqual(1, len(diff.structure.text_facts))
        self.assertEqual(1, len(diff.structure.timestamp_facts))
        self.assertEqual(1, len(diff.structure.image_facts))
        self.assertEqual(1, len(diff.structure.file_facts))
        self.assertEqual(1, len(diff.structure.json_facts))
        self.assertEqual(1, len(diff.structure.boolean_facts))
        self.assertEqual(1, len(diff.structure.dimensions))
        self.assertEqual(1, len(diff.indexes))

        self.assertEqual(1, len(diff.consumers))

    def test_deleted_data_series_no_delete_in_base_default(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_deleted_data_series_no_delete_in_base(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_data_series(base, target, delete_in_base=False)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_deleted_data_series_delete_in_base(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_data_series(base, target, delete_in_base=True)
        self.assertIsNotNone(diff.data_series)
        self.assertEqual(OperationType.DELETE, diff.data_series.operation_type)
        self.assertEqual(base.data_series.to_dict(), diff.data_series.payload)
        self.assertEqual(1, len(diff.structure.float_facts))
        self.assertEqual(1, len(diff.structure.string_facts))
        self.assertEqual(1, len(diff.structure.text_facts))
        self.assertEqual(1, len(diff.structure.timestamp_facts))
        self.assertEqual(1, len(diff.structure.image_facts))
        self.assertEqual(1, len(diff.structure.file_facts))
        self.assertEqual(1, len(diff.structure.json_facts))
        self.assertEqual(1, len(diff.structure.boolean_facts))
        self.assertEqual(1, len(diff.structure.dimensions))
        self.assertEqual(1, len(diff.indexes))

        self.assertEqual(1, len(diff.consumers))

    def test_empty_diff_on_same(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_data_series_diff_is_update(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        target.data_series.name = 'some_other_name'

        diff = diff_data_series(base, target)
        self.assertIsNotNone(diff.data_series)
        self.assertEqual(OperationType.UPDATE, diff.data_series.operation_type)
        self.assertEqual(target.data_series.to_dict(), diff.data_series.payload)

    def test_empty_diff_on_only_data_series(self) -> None:
        base = DataSeriesDefinition(
            data_series=DataSeries(
                external_id='my_ds',
                name='my_ds',
                backend='DYNAMIC_SQL',
                extra_config={
                    "auto_clean_history_after_days": -1,
                    "auto_clean_meta_model_after_days": -1
                },
                allow_extra_fields=True
            ),
            structure=DataSeriesStructure()
        )
        target = base

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_float(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.float_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(1, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_string(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.string_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(1, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_text(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.text_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(1, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_timestamp(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.timestamp_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(1, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_image(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.image_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(1, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_file(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.file_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(1, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_json(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.json_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(1, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_boolean(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.boolean_facts = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(1, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_dimension(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.structure.dimensions = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(1, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_index_remove(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.indexes = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(1, len(diff.indexes))
        self.assertEqual(OperationType.DELETE,diff.indexes[0].operation_type)

        self.assertEqual(0, len(diff.consumers))

    def test_diff_index_add(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        base.indexes = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(1, len(diff.indexes))
        self.assertEqual(OperationType.CREATE,diff.indexes[0].operation_type)

        self.assertEqual(0, len(diff.consumers))

    def test_diff_index_update(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        base.indexes = [Index(
                    external_id='index',
                    name='index_minimally_different',
                    targets=[
                        IndexTarget(
                            target_external_id='image',
                            target_type='IMAGE_FACT'
                        ),
                        IndexTarget(
                            target_external_id='boolean',
                            target_type='BOOLEAN_FACT'
                        )
                    ]
                )]

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(1, len(diff.indexes))
        self.assertEqual(OperationType.UPDATE,diff.indexes[0].operation_type)

        self.assertEqual(0, len(diff.consumers))

    def test_diff_index_recreate(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        base.indexes = [Index(
                    external_id='index',
                    name='index',
                    targets=[
                        IndexTarget(
                            target_external_id='image_minimally_different',
                            target_type='IMAGE_FACT'
                        ),
                        IndexTarget(
                            target_external_id='boolean',
                            target_type='BOOLEAN_FACT'
                        )
                    ]
                )]

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(2, len(diff.indexes))
        self.assertEqual(OperationType.DELETE,diff.indexes[0].operation_type)
        self.assertEqual(OperationType.CREATE,diff.indexes[1].operation_type)

        self.assertEqual(0, len(diff.consumers))

    def test_diff_consumers_no_remove_missing(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.consumers = []

        diff = diff_data_series(base, target, remove_missing_consumers=False)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(0, len(diff.consumers))

    def test_diff_consumers_default(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()
        target.consumers = []

        diff = diff_data_series(base, target)
        self.assertIsNone(diff.data_series)
        self.assertEqual(0, len(diff.structure.float_facts))
        self.assertEqual(0, len(diff.structure.string_facts))
        self.assertEqual(0, len(diff.structure.text_facts))
        self.assertEqual(0, len(diff.structure.timestamp_facts))
        self.assertEqual(0, len(diff.structure.image_facts))
        self.assertEqual(0, len(diff.structure.file_facts))
        self.assertEqual(0, len(diff.structure.json_facts))
        self.assertEqual(0, len(diff.structure.boolean_facts))
        self.assertEqual(0, len(diff.structure.dimensions))
        self.assertEqual(0, len(diff.indexes))

        self.assertEqual(1, len(diff.consumers))
