# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.lint import sql_cursor


def user_exists(role: str, connection_name: str) -> bool:
    with sql_cursor(connection_name) as cursor:
        cursor.execute(f'''
            SELECT count(*) FROM "pg_roles" WHERE "rolname"=%(role_name)s
            ''', {
            "role_name": role
        })
        res = cursor.fetchone()[0]
        ret: bool = res == 1
        return ret
