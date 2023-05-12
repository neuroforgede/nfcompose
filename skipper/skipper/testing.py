# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import os

SKIPPER_CELERY_TESTING: bool = os.getenv('SKIPPER_CELERY_TESTING', 'False') in ['true', 'True']
SKIPPER_TESTING: bool = os.getenv('SKIPPER_TESTING', 'False') in ['true', 'True']
