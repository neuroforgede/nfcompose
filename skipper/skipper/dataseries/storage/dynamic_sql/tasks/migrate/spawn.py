# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Union

from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.task_data import MetaModelTaskData
from skipper.dataseries.tasks.metamodel import spawn_meta_model_task
from skipper.dataseries.raw_sql import dbtime
from skipper.core.middleware import get_current_request
from django.http import HttpRequest
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from skipper.testing import SKIPPER_CELERY_TESTING
from django.db import transaction


def spawn_migrate_task(
    data_series: DataSeries,
    task_name: str
) -> None:
    _current_request: HttpRequest = get_current_request()
    _user: Union[AbstractBaseUser, AnonymousUser] = _current_request.user
    meta_model_task_data = MetaModelTaskData.objects.create(
        tenant=data_series.tenant,
        task=task_name,
        data_series = data_series,
        point_in_time=dbtime.now(),
        data={},
        user=_user if _user is not None else None,
        record_source='REST API' if _current_request is not None else None
    )

    if SKIPPER_CELERY_TESTING:
        # when testing, immediately run the code,
        # as we are in the same transaction always
        spawn_meta_model_task(
            task_data_id=meta_model_task_data.id
        )
    else:
        transaction.on_commit(
            lambda: spawn_meta_model_task(meta_model_task_data.id)
        )