# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from skipper import modules


def skipper_base_name(basename: str) -> str:
    return f'skipper-{modules.url_representation(modules.Module.FLOW)}-{basename}'


def component_root(component: str) -> str:
    return skipper_base_name(f'{component}-api-root')


root_view_base_name = skipper_base_name('api-root')

flow_options_base_name = skipper_base_name('flow-options')

node_red_base_impl_base_name = skipper_base_name('flow-impl')
node_red_base_public_impl_base_name = skipper_base_name('flow-public-impl')

system_engine_access_base_name = skipper_base_name('system-engine-access')

engine_view_base_name = skipper_base_name('engine')
engine_secret_view_base_name = skipper_base_name('engine-secret')
engine_access_view_base_name = skipper_base_name('engine-access')
engine_permission_user_base_name = skipper_base_name('engine-permission-user')
engine_permission_group_base_name = skipper_base_name('engine-permission-group')

http_endpoint_view_base_name = skipper_base_name('http-endpoint')
http_endpoint_permission_user_base_name = skipper_base_name('http-endpoint-permission-user')
http_endpoint_permission_group_base_name = skipper_base_name('http-endpoint-permission-group')

