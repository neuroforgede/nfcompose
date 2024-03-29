# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from skipper import modules


def skipper_base_name(basename: str) -> str:
    return f'skipper-{modules.url_representation(modules.Module.DEBUG)}-{basename}'


def component_root(component: str) -> str:
    return skipper_base_name(f'{component}-api-root')


root_view_base_name = skipper_base_name('api-root')

telemetry_ui_auth_view_base_name = skipper_base_name('telemetry-ui-auth')
