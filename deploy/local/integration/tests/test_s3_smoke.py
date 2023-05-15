from typing import Any, Dict
from library.base_test import BaseIntegrationTest
from pathlib import Path

class S3Smoke(BaseIntegrationTest):
    data_series: Dict[str, Any]
    file_fact: Dict[str, Any]

    def setUp(self) -> None:
        super().setUp()

        self.data_series = self._create_data_series(
            external_id='s3_smoke',
            name='s3_smoke'
        )
        self.file_fact = self.client.post(
            self.data_series['file_facts'],
            data={
                "external_id": 'file_fact',
                "name": 'file_fact',
                "optional": False
            }
        )
    
    def test(self) -> None:
        data_point = self.client.post_multipart(
            url=self.data_series['data_points'],
            data={
                "external_id": (None, "112123s"),
                "payload.file_fact": open(f'{Path(__file__).parent}/resources/testfile.txt')
            }
        )
        print(data_point)
