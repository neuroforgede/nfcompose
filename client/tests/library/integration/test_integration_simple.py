# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from tests.base_test import BaseIntegrationTest

class IntegrationConnectionTest(BaseIntegrationTest):
    def test_connect_to_test_db(self) -> None:
        '''Connection to integration test location established?'''
        # if this test fails, we have a hint that it's an issue with the integration
        # no body needed, setUp would fail anyway
        pass