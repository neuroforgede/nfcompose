# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.http import HttpResponse
from rest_framework import status
from typing import Optional

from skipper import modules
from skipper.core.tests.base import BASE_URL, BaseRESTPermissionTest

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class PruneDataSeriesViewTest(BaseRESTPermissionTest):
    """
    tests whether the storage backend permissions work properly
    """
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'prune/dataseries/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'dataseries'

    def permission_code_name(self) -> str:
        return 'prune_data_series'

    def method_under_test_malformed(self) -> Optional[HttpResponse]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> HttpResponse:
        return self.user_client.post(
            path=self.url_under_test,
            data={
                "older_than": "2020-12-10T14:29:11.217417Z"
            },
            format='json'
        )
