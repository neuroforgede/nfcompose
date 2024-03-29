# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import os

TESTING = os.getenv('TESTING', 'false') == 'true'

USER_NAME = str
HTTP_METHOD = str

TEST_NF_COMPOSE_URL = os.getenv('TEST_NF_COMPOSE_URL', 'http://skipper.test.local:8000')
TEST_USER_NAME = os.getenv('TEST_USER_NAME', 'admin')
TEST_USER_PASSWORD = os.getenv('TEST_USER_NAME', 'admin')
