# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import re


def validate_string(string: str) -> bool:
    regex = re.compile('[a-zA-Z0-9_]+')
    return regex.fullmatch(string) is not None


def validate_sql_string(string: str) -> bool:
    regex = re.compile('[a-zA-Z0-9_\-"]+')
    return regex.fullmatch(string) is not None