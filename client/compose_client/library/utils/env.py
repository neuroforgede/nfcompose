# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import os
import threading
from typing import Dict, Any

TESTING = os.getenv('TESTING', 'false') == 'true'

# not really an env var, but we need this in a central place
# to disable/enable mock behaviour for unit tests
global_data = threading.local()

global_data.UNIT_TESTING = False

USER_NAME = str
HTTP_METHOD = str

MOCK_RESPONSES = Dict[USER_NAME, Dict[HTTP_METHOD, Dict[str, Any]]]


def set_mock_responses(responses: Dict[USER_NAME, Dict[HTTP_METHOD, Dict[str, Any]]]) -> None:
    global_data.MOCK_RESPONSES = responses


def get_mock_responses() -> Dict[USER_NAME, Dict[HTTP_METHOD, Dict[str, Any]]]:
    return getattr(global_data, 'MOCK_RESPONSES', dict())  # type: ignore
