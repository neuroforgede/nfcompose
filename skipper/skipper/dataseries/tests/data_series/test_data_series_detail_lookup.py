# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesByIdLookup(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = False

    def test_no_uuid(self) -> None:
        bad_id = '4'
        should_404 = self.client.get(DATA_SERIES_BASE_URL + 'dataseries/' + bad_id + '/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, should_404.status_code)

    def test_by_external_id_not_found(self) -> None:
        bad_id = 'some_external_id'
        should_404 = self.client.get(DATA_SERIES_BASE_URL + 'by-external-id/dataseries/' + bad_id + '/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, should_404.status_code)

    def test_sub_no_uuid(self) -> None:
        bad_id = '4'
        should_404 = self.client.get(DATA_SERIES_BASE_URL + 'dataseries/' + bad_id + '/datapoint/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, should_404.status_code)

    def test_sub_by_external_id_not_found(self) -> None:
        bad_id = 'some_external_id'
        should_404 = self.client.get(DATA_SERIES_BASE_URL + 'by-external-id/dataseries/' + bad_id + '/datapoint/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, should_404.status_code)
