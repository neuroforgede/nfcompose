# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from compose_client.library.service.diff import diff_datapoint, diff_datapoint_list
from compose_client.library.models.operation.general import OperationType
from compose_client.library.models.definition.datapoint import DataPoint, FileTypeContent
from compose_client.library.models.definition.facts import FileFact, ImageFact
from compose_client.library.models.definition.data_series_definition import DataSeriesStructure
from compose_client.library.models.diff.datapoint_operation import DataPointOperation
import unittest

class TestDataPointDiff(unittest.TestCase):

    def setUp(self) -> None:
        self.base_datapoints = [
            DataPoint(external_id='test_datapoint_0', payload={}),  # index 0
            DataPoint(external_id='test_datapoint_1', payload={'foo': 'bar'}),      # index 1
            DataPoint(external_id='test_datapoint_2', payload={'foo': 'bar', 'foobar': 'baz'}),     # index 2
            DataPoint(external_id='test_datapoint_3', payload={})   # index 3
            # test_datapoint_4
        ]

        self.target_datapoints = [
            DataPoint(external_id='test_datapoint_0', payload={}),      # index 0
            DataPoint(external_id='test_datapoint_1', payload={'foo': 'boom'}),     # index 1
            DataPoint(external_id='test_datapoint_2', payload={'foo': 'bar', 'foobar': 'baz'}),     # index 2
            # test_datapoint_3
            DataPoint(external_id='test_datapoint_4', payload={})   # index 3
        ]

        self.dataseries_structure_with_files = DataSeriesStructure(
            file_facts=[FileFact(external_id='why_is_here_a_file?', name='why_is_here_a_file?', optional=False)]
        )

        self.dataseries_structure_with_images = DataSeriesStructure(
            image_facts=[ImageFact(external_id='why_is_here_an_image?', name='why_is_here_an_image?', optional=False)]
        )

        self.diff_datapoint_list_results = [
            # test_datapoint_0
            DataPointOperation(operation_type=OperationType.UPDATE, datapoint=self.target_datapoints[1]),    # test_datapoint_1
            # test_datapoint_2
            DataPointOperation(operation_type=OperationType.DELETE, datapoint=DataPoint(external_id=self.base_datapoints[3].external_id, payload={})),   # test_datapoint_3
            DataPointOperation(operation_type=OperationType.CREATE, datapoint=self.target_datapoints[3])    # test_datapoint_4
        ]
        self.wrong_parameter = [
            DataPoint(external_id='test_datapoint_0', payload={}),
            DataPoint(external_id='test_datapoint_0', payload={}),
            DataPoint(external_id='test_datapoint_0', payload={})
        ]

        self.base_filefact_test = [
            DataPoint(external_id='file_datapoint_0', payload={'file_fact': FileTypeContent(url='https://preview.redd.it/niov5u1cfcq61.jpg?width=960&crop=smart&auto=webp&s=7add83352a08c5b0a14cc6d690da3c906a260d30')}),
            DataPoint(external_id='file_datapoint_1', payload={'file_fact': FileTypeContent(url='https://preview.redd.it/sec9nhh2urk01.png?width=960&crop=smart&auto=webp&s=b67c673e4f0c2aa4e724e386cfa3aca52e2bcab5')})
        ]

        self.target_filefact_test = [
            DataPoint(external_id='file_datapoint_0', payload={'file_fact': FileTypeContent(url='https://preview.redd.it/niov5u1cfcq61.jpg?width=960&crop=smart&auto=webp&s=7add83352a08c5b0a14cc6d690da3c906a260d30')}),
            DataPoint(external_id='file_datapoint_1', payload={'file_fact': FileTypeContent(url='https://raw.githubusercontent.com/neuroforgede/docker-swarm-tools/main/LICENSE')})
        ]

    def test_diff_datapoint(self) -> None:
        self.assertFalse(diff_datapoint(base_datapoint=self.base_datapoints[0], target_datapoint=self.target_datapoints[0], dataseries_structure=DataSeriesStructure()))   # succeed if datapoints are equal
        self.assertTrue(diff_datapoint(base_datapoint=self.base_datapoints[1], target_datapoint=self.target_datapoints[1], dataseries_structure=DataSeriesStructure()))    # succeed if datapoints are not equal

    def test_diff_datapoint_file_and_image_fact(self) -> None:
        # tests if exception is thrown, beacause of missing feature:
        with self.assertRaises(NotImplementedError):
            diff_datapoint(base_datapoint=self.base_filefact_test[0], target_datapoint=self.target_filefact_test[0], dataseries_structure=self.dataseries_structure_with_files)
        
        with self.assertRaises(NotImplementedError):
            diff_datapoint(base_datapoint=self.base_filefact_test[0], target_datapoint=self.target_filefact_test[0], dataseries_structure=self.dataseries_structure_with_images)

        # tests, for when the feature is implemented;
        # self.assertFalse(diff_datapoint(base_datapoint=self.base_filefact_test[0], target_datapoint=self.target_filefact_test[0]))
        # self.assertTrue(diff_datapoint(base_datapoint=self.base_filefact_test[1], target_datapoint=self.target_filefact_test[1]))

    def test_diff_datapoint_list(self) -> None:

        def datapointoperation_get_external_id(operation: DataPointOperation) -> str:
            return operation.datapoint.external_id

        self.assertTrue(
            self.diff_datapoint_list_results.sort(key=datapointoperation_get_external_id)
            ==
            diff_datapoint_list(
                base_datapoints=self.base_datapoints,
                target_datapoints=self.target_datapoints,
                dataseries_structure=DataSeriesStructure()
            ).sort(key=datapointoperation_get_external_id)
        )

        with self.assertRaises(ValueError):
            diff_datapoint_list(
                base_datapoints=self.base_datapoints,
                target_datapoints=self.wrong_parameter,
                dataseries_structure=DataSeriesStructure()
            )

        with self.assertRaises(ValueError):
            diff_datapoint_list(
                base_datapoints=self.wrong_parameter,
                target_datapoints=self.target_datapoints,
                dataseries_structure=DataSeriesStructure()
            )
