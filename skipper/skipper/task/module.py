# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.conf.urls import include
from django.urls import path
from rest_framework import routers
from typing import Any, List, Dict

from skipper import modules
from skipper.core.utils.router import DefaultRouter
from skipper.core.views import mixin
from skipper.core.views.module import APIOverviewView
from skipper.task import constants
from skipper.task.views import task_queue_list, task_dashboard_auth, task_queue_overview

def get_module() -> modules.Module:
    return modules.Module.TASK


def get_root_view_base_name() -> str:
    return constants.root_view_base_name


class TaskAPIView(mixin.AllowedToBrowseAPIViewMixin, routers.APIRootView):
    """
    The Task API
    """


class TaskRouter(DefaultRouter):
    APIRootView = TaskAPIView

    # only needed for component style modules
    # root_view_name = constants.data_root_view_base_name
    root_view_name = constants.root_view_base_name

    skipper_base_name = constants.root_view_base_name


def get_urls(module_settings: Dict[str, Any]) -> List[Any]:
    _listed_views: Dict[str, Any] = {
        'queue': constants.task_queue_view_overview_name,
        'dashboard': constants.task_dashboard_auth_view_base_name + '-root'
    }

    class TaskAPIView(APIOverviewView):
        """
        Overview for the Task API
        """
        skipper_base_name = constants.root_view_base_name
        listed_views = _listed_views

    router = TaskRouter()

    urls = [
        path('', TaskAPIView.as_view(), name=TaskAPIView.skipper_base_name),
        path('queue/', task_queue_overview, name=constants.task_queue_view_overview_name),
        path('queue/<str:queue_name>/', task_queue_list, name=constants.task_queue_view_base_name + '-list'),
        path('dashboard/', task_dashboard_auth, name=constants.task_dashboard_auth_view_base_name + '-root'),
        path(
            '',
            include(router.urls)
        ),
    ]

    return urls
