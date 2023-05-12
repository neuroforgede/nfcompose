# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import cast

from django.db import connections
from psycopg2.extensions import quote_ident  # type: ignore
from rest_framework.exceptions import APIException

from skipper.dataseries.raw_sql.validate import validate_sql_string


def escape(string: str, connection_name: str = 'default') -> str:
    if not validate_sql_string(string):
        raise APIException('SQL may only contain a-zA-Z0-9_%\'()-" .')
    with connections[connection_name].cursor() as cursor:
        return cast(str, quote_ident(string, cursor.cursor))
