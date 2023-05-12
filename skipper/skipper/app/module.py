# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any, List, Dict

from django.urls import path, re_path

from skipper import modules
from skipper.app import views


def get_module() -> modules.Module:
    return modules.Module.APP


def get_root_view_base_name() -> str:
    return 'app-root'


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    urls = [
        path('__integrate__auth__/', views.app_view, name='app-root'),
    ]
    return urls
