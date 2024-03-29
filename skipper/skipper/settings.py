# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


# first load settings that were set for dev (if any)
from skipper.environment_local import *
from skipper.settings_env import *
# TODO: maybe do this in env vars as well?
from skipper.settings_features import *
from skipper.settings_custom import *
