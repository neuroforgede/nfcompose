# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from skipper.core.views.mixin import HasTenantSetPermission
from skipper.dataseries.views.common import HasDataSeriesGlobalReadPermission

metamodel_base_line_permissions = [
    HasTenantSetPermission,
    HasDataSeriesGlobalReadPermission,
]
