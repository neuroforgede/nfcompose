# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from skipper import modules


def skipper_base_name(basename: str) -> str:
    return f'skipper-{modules.url_representation(modules.Module.CORE)}-{basename}'


def component_root(component: str) -> str:
    return skipper_base_name(f'{component}-api-root')

ANONYMOUS_USER_NAME = "AnonymousUser"

core_root_view_base_name = skipper_base_name('api-root')

core_tenant_view_set_name = skipper_base_name('tenant')
core_tenant_user_view_set_name = skipper_base_name('tenant_user')
core_user_view_set_name = skipper_base_name('user')
core_user_permission_view_set_name = skipper_base_name('user-permission')
