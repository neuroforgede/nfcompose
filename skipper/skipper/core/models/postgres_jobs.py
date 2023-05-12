# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import time

import datetime
from django.db import IntegrityError, transaction, connection
from django.db.models import DO_NOTHING, ForeignKey
from django.db.models.fields import CharField
from django_multitenant.mixins import TenantModelMixin  # type: ignore
from django_multitenant.models import TenantManager  # type: ignore
from pgq import models as pgq_models
from pgq import queue as pgq_queue
from pgq.exceptions import PgqException
from typing import Callable, Any, Dict, Optional, Iterable, Tuple, cast, Sequence, TypeVar, TYPE_CHECKING

from skipper.core.models.tenant import get_tenant_model, Tenant


class _BaseJob(pgq_models.BaseJob):
    globally_unique_identifier = CharField(unique=True, max_length=1024, blank=False, null=True)
    queue = CharField(
        max_length=1024,
        null=False,
        help_text="Use a unique name to represent each queue.",
    )

    class Meta:
        abstract = True


class TenantPostgresQueueJob(TenantModelMixin, _BaseJob):  # type: ignore
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING)

    objects: TenantManager = TenantManager()

    @property
    def tenant_field(self) -> str:
        return 'tenant_id'

    @classmethod
    def dequeue_tenant(
        cls,
        exclude_ids: Optional[Iterable[int]],
        tasks: Optional[Sequence[str]],
        queue: str,
        tenant: Tenant
    ) -> Optional['TenantPostgresQueueJob']:
        """
        Claims the first available task and returns it. If there are no
        tasks available, returns None.

        exclude_ids: Iterable[int] - excludes jobs with these ids
        tasks: Optional[Sequence[str]] - filters by jobs with these tasks.

        For at-most-once delivery, commit the transaction before
        processing the task. For at-least-once delivery, dequeue and
        finish processing the task in the same transaction.

        To put a job back in the queue, you can just call
        .save(force_insert=True) on the returned object.
        """

        WHERE = "WHERE execute_at <= now() AND NOT id = ANY(%s) AND queue = %s AND tenant_id = %s"
        args = [[] if exclude_ids is None else list(exclude_ids), queue, tenant.id]
        if tasks is not None:
            WHERE += " AND TASK = ANY(%s)"
            args.append(tasks)

        jobs = list(
            cls.objects.raw(
                """
            DELETE FROM {db_table}
            WHERE id = (
                SELECT id
                FROM {db_table}
                {WHERE}
                ORDER BY priority DESC, created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING *;
            """.format(
                    db_table=connection.ops.quote_name(cls._meta.db_table), WHERE=WHERE
                ),
                args,
            )
        )
        assert len(jobs) <= 1
        if jobs:
            return cast(TenantPostgresQueueJob, jobs[0])
        else:
            return None

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "execute_at": self.execute_at,
            "priority": self.priority,
            "queue": self.queue,
            "task": self.task,
            "args": self.args,
            "tenant": self.tenant
        }

    class Meta:
        db_table = '_core_tenant_pgq_job'


class BaseTenantQueue(pgq_queue.BaseQueue[TenantPostgresQueueJob]):
    tenant: Tenant
    heartbeat: bool
    job_model = TenantPostgresQueueJob

    def __init__(
            self,
            tasks: Dict[str, Callable[['BaseTenantQueue', TenantPostgresQueueJob], Any]],
            queue: str,
            tenant: Tenant,
            heartbeat: bool
    ) -> None:
        # we dont use the notify feature just yet
        # we can however add it if we really need it
        super().__init__(tasks, None, queue)
        self.tenant = tenant
        self.heartbeat = heartbeat

    def listen(self) -> None:
        raise AssertionError()

    def notify(self) -> None:
        raise AssertionError()

    def _run_once(  # type: ignore
        self, exclude_ids: Optional[Iterable[int]] = None
    ) -> Optional[Tuple[Any, Any]]:
        """Get a job from the queue and run it, but tenant aware.

            Returns:
                - if a job was run: the Job obj run (now removed from the db) and
                  it's returned values.
                - If there was no job, return None.

            If a job fails, ``PgqException`` is raised with the job object that
            failed stored in it.
            """
        job = self.job_model.dequeue_tenant(
            exclude_ids=exclude_ids,
            queue=self.queue,
            tasks=list(self.tasks),
            tenant=self.tenant
        )
        if job:
            self.logger.debug(
                "Claimed %r.", job, extra={"data": {"job": job.to_json(), }}
            )
            try:
                return job, self.run_job(job)
            except Exception as e:
                # Add job info to exception to be accessible for logging.
                raise PgqException(job=job) from e
        else:
            return None

    def run_once(
        self, exclude_ids: Optional[Iterable[int]] = None
    ) -> Optional[Tuple[TenantPostgresQueueJob, Any]]:
        raise NotImplementedError()

    def run_job(self, job: TenantPostgresQueueJob) -> Any:
        """Execute job, return the output of job."""
        task = self.tasks[job.task]
        start_time = time.time()
        retval = task(cast(Any, self), job)
        self.logger.info(
            "%r: Processing %r took %0.4f seconds. Task returned %r.",
            self.queue,
            job,
            time.time() - start_time,
            retval,
            extra={"data": {"job": job.to_json(), "retval": retval,}},
        )
        return retval

    def enqueue(
            self,
            task: str,
            args: Optional[Dict[str, Any]] = None,
            execute_at: Optional[datetime.datetime] = None,
            priority: Optional[int] = None
        ) -> TenantPostgresQueueJob:
        assert task in self.tasks
        if args is None:
            args = {}

        _should_enqueue = True

        kwargs: Dict[str, Any] = {
            "task": task,
            "args": args,
            "queue": self.queue,
            "tenant": self.tenant
        }
        if execute_at is not None:
            kwargs["execute_at"] = execute_at
        if priority is not None:
            kwargs["priority"] = priority

        if self.heartbeat:
            task_globally_unique_identifier = f'{self.queue}_{task}'
            _should_enqueue = not self.job_model.objects.filter(
                globally_unique_identifier=task_globally_unique_identifier,
                tenant=self.tenant
            ).exists()
            kwargs["globally_unique_identifier"] = task_globally_unique_identifier

        if _should_enqueue:
            if self.heartbeat:
                try:
                    with transaction.atomic():
                        job = self.job_model.objects.create(**kwargs)
                except IntegrityError as e:
                    # should not have put the task in the queue in the first place
                    return cast(TenantPostgresQueueJob, None)  # hack
            else:
                job = self.job_model.objects.create(**kwargs)
            if self.notify_channel:
                self.notify()
            return cast(TenantPostgresQueueJob, job)
        else:
            return cast(TenantPostgresQueueJob, None)  # hack


class TenantAtMostOnceQueue(BaseTenantQueue):
    def run_once(
        self, exclude_ids: Optional[Iterable[int]] = None
    ) -> Optional[Tuple[TenantPostgresQueueJob, Any]]:
        assert not connection.in_atomic_block
        return self._run_once(exclude_ids=exclude_ids)


class TenantAtLeastOnceQueue(BaseTenantQueue):
    @transaction.atomic
    def run_once(
        self, exclude_ids: Optional[Iterable[int]] = None
    ) -> Optional[Tuple[TenantPostgresQueueJob, Any]]:
        return self._run_once(exclude_ids=exclude_ids)
