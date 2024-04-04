# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.db.models import Model
from typing import Dict, Any, List, cast


class TaskPermissions(Model):
    """
    global task permissions, not really a model
    that stores any real data
    """
    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model
        default_permissions: List[str] = []
        permissions = (
            ('dashboard', 'Allowed to view the task dashboard'),
        )


class TaskData:
    id: str
    payload: Dict[str, Any]

    def __init__(self, id: str, payload: Dict[str, Any]):
        self.id = id
        self.payload = payload


def get_task_data_count(queue_name: str) -> int:
    # Get a configured instance of a celery app:
    from skipper.celery import app as celery_app

    with celery_app.pool.acquire(block=True) as conn:
        return cast(int, conn.default_channel.client.llen(queue_name))


def get_task_data(page: int, pagesize: int, queue_name: str) -> List[Any]:
    import base64
    import json

    # Get a configured instance of a celery app:
    from skipper.celery import app as celery_app

    with celery_app.pool.acquire(block=True) as conn:
        tasks = conn.default_channel.client.lrange(queue_name, page * pagesize, (page + 1) * pagesize - 1)
        decoded_tasks = []

    for task in tasks:
        j = json.loads(task)
        j['body'] = json.loads(base64.b64decode(j['body']))
        decoded_tasks.append(TaskData(id=j['headers']['id'], payload=j))

    return decoded_tasks
