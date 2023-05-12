# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Any, Optional

import re

from skipper import settings
from skipper.core.middleware import get_current_request

bulk_endpoint_regex = r'^\/api\/dataseries\/(?:by-external-id\/)?dataseries\/[^\/]*\/bulk\/datapoint\/.*$'


class DynamicSQLRouter:

    def db_for_read(self, model: Any, **hints: Any) -> Optional[str]:
        request = get_current_request()
        # if we ever change the behaviour here, we have to adapt
        # storage_view_adapter to use that connection for transactions
        if request is not None and \
                hasattr(settings, 'DATA_SERIES_DYNAMIC_SQL_DB_BULK') and \
                re.match(bulk_endpoint_regex, request.path):
            return settings.DATA_SERIES_DYNAMIC_SQL_DB_BULK
        return 'default'

    def db_for_write(self, model: Any, **hints: Any) -> Optional[str]:
        request = get_current_request()
        # if we ever change the behaviour here, we have to adapt
        # storage_view_adapter to use that connection for transactions
        if request is not None and \
                hasattr(settings, 'DATA_SERIES_DYNAMIC_SQL_DB_BULK') and \
                re.match(bulk_endpoint_regex, request.path):
            return settings.DATA_SERIES_DYNAMIC_SQL_DB_BULK
        return 'default'

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> Optional[bool]:
        return None

    def allow_migrate(self, db: Any, app_label: Any, model_name: Optional[Any] = None, **hints: Any) -> Optional[bool]:
        return None
