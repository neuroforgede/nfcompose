# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
from django.utils import dateparse
from typing import Any, Optional


class PointInTimeMixin(object):
    request: Any
    history: bool = False

    def get_point_in_time(self) -> Optional[datetime.datetime]:
        point_in_time: Optional[datetime.datetime] = None
        if self.history and 'point_in_time' in self.request.GET:
            point_in_time_val = self.request.GET['point_in_time']
            # FIXME: should we throw a ValidationError here?
            try:
                if point_in_time_val is not None:
                    point_in_time = dateparse.parse_datetime(point_in_time_val)
            except ValueError:
                point_in_time = None
        return point_in_time

    def get_changes_since(self) -> Optional[datetime.datetime]:
        changes_since: Optional[datetime.datetime] = None
        if 'changes_since' in self.request.GET:
            changes_since_val = self.request.GET['changes_since']
            # FIXME: should we throw a ValidationError here?
            try:
                if changes_since_val is not None:
                    changes_since = dateparse.parse_datetime(changes_since_val)
            except ValueError:
                changes_since = None
        return changes_since

    def should_include_versions(self) -> bool:
        if self.history and 'include_versions' in self.request.GET:
            include_versions = self.request.GET['include_versions']
            if include_versions is None or include_versions == '' or include_versions == 'true':
                return True
        return False
