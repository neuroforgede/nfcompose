# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from skipper import modules


def skipper_base_name(basename: str) -> str:
    return f'skipper-{modules.url_representation(modules.Module.COMMON)}-{basename}'


def component_root(component: str) -> str:
    return skipper_base_name(f'{component}-api-root')


common_root_view_base_name = skipper_base_name('api-root')
common_auth_root_view_base_name = component_root('auth')

common_auth_user_view_set_name = skipper_base_name('auth-user')
common_auth_user_permission_view_set_name = skipper_base_name('auth-user-permission')
common_auth_group_view_set_name = skipper_base_name('auth-group')
common_auth_group_permission_view_set_name = skipper_base_name('auth-group-permission')

common_auth_jwt_root_view_name = skipper_base_name('jwt-root')
common_auth_jwt_obtain_pair_view_name = skipper_base_name('jwt-obtain-pair')
common_auth_jwt_refresh_view_name = skipper_base_name('jwt-refresh')
common_auth_jwt_verify_view_name = skipper_base_name('jwt-verify')
common_auth_jwt_blacklist_view_name = skipper_base_name('jwt-blacklist')

common_tenant_tenant_view_base_name = skipper_base_name('tenant')

common_dataseries_component_id = '0'
