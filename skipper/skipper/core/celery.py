# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging
from functools import wraps

from celery import current_app  # type: ignore
from celery.app.task import TaskType, Task  # type: ignore
from celery.exceptions import TaskPredicate, Reject  # type: ignore
from celery.worker.request import Request  # type: ignore
from typing import Any, Dict


from skipper.testing import SKIPPER_CELERY_TESTING

logger = logging.getLogger(__name__)


class SkipperCeleryRequest(Request):  # type: ignore

    def on_timeout(self, soft: bool, timeout: Any) -> None:
        super(SkipperCeleryRequest, self).on_timeout(soft, timeout)

    def on_failure(self, exc_info: Any, send_failed_event: bool = True, return_ok: bool = False) -> None:
        super(SkipperCeleryRequest, self).on_failure(
            exc_info,
            send_failed_event=send_failed_event,
            return_ok=return_ok
        )


class SkipperCeleryTask(Task, metaclass=TaskType):  # type: ignore
    Request = SkipperCeleryRequest

    def delay(self, *args, **kwargs):  # type: ignore
        """Star argument version of :meth:`apply_async`.

        Does not support the extra options enabled by :meth:`apply_async`.

        Arguments:
            *args (Any): Positional arguments passed on to the task.
            **kwargs (Any): Keyword arguments passed on to the task.
        Returns:
            celery.result.AsyncResult: Future promise.
        """
        print('delay' + str(kwargs))
        return super().apply_async(args, kwargs)

    def on_success(self, retval: Any, task_id: str, args: Any, kwargs: Dict[str, Any]) -> None:
        super(SkipperCeleryTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc: Any, task_id: str, args: Any, kwargs: Dict[str, Any], einfo: Any) -> None:
        super(SkipperCeleryTask, self).on_failure(exc, task_id, args, kwargs, einfo)


if SKIPPER_CELERY_TESTING:
    def task(*args: Any, **kwargs: Any) -> Any:
        class SyncDelayTask(SkipperCeleryTask, metaclass=TaskType):  # type: ignore
            """
            for testing force the use of synchronous tasks
            """

            def delay(self, *args: Any, **kwargs: Any) -> Any:
                return self.apply(args, kwargs)

            def apply_async(self, args=None, kwargs=None, task_id=None, producer=None, link=None, link_error=None, shadow=None, **options): # type: ignore
                return super().apply(args, kwargs, link, link_error, task_id, **options)

        return current_app.task(*args, **dict({'base': SyncDelayTask}, **kwargs))
else:
    task = current_app.task


def acquire_semaphore(semaphore_key: str, concurrency_limit: int, lock_timeout: int) -> bool:
    """Attempt to acquire a semaphore for the given semaphore_key."""
    from skipper.celery import app as celery_app

    with celery_app.pool.acquire(block=True) as conn:
        redis_client = conn.default_channel.client

        key = f"semaphore:{semaphore_key}"
        # Initialize the semaphore with an expiry if it doesn't exist
        current_value = redis_client.get(key)
        if current_value is None:
            redis_client.set(key, 0, nx=True, ex=lock_timeout)

        # Atomically increment the count
        count = redis_client.incr(key)
        if count > concurrency_limit:
            # Decrement back if we exceed the limit and return False
            redis_client.decr(key)
            return False
        return True

def release_semaphore(semaphore_key: str) -> None:
    """Release the semaphore for the given semaphore_key."""
    from skipper.celery import app as celery_app

    with celery_app.pool.acquire(block=True) as conn:
        redis_client = conn.default_channel.client
        key = f"semaphore:{semaphore_key}"
        # Decrement the count to release a permit
        redis_client.decr(key)
        
        redis_val = redis_client.get(key)
        # Reset the semaphore if it goes to zero
        if redis_val is not None and int(redis_val) <= 0:
            redis_client.delete(key)