# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging
from typing import Any


from opentelemetry import trace  # type: ignore
from django.db import transaction
from random import shuffle
from skipper.core.celery import task
from skipper.core.models.tenant import Tenant

from skipper.core.models.postgres_jobs import BaseTenantQueue, TenantPostgresQueueJob
from skipper.dataseries.tasks.pgq import get_queue, try_run_all

from skipper.dataseries.models.metamodel.consumer import Consumer, DataSeries_Consumer
from skipper import environment_common
from skipper.dataseries.models import try_send_events

logger = logging.getLogger(__name__)


def consumer_heartbeat(queue: BaseTenantQueue, job: TenantPostgresQueueJob) -> Any:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span('skipper.dataseries.tasks.consumer_heartbeat'):
        args = job.args
        try:
            consumer = Consumer.objects.get(id=args['consumer_id'])
        except:
            return None
        
        total_sent_count: int = 0
        # by default back off every 200 events
        # this ensures a snappier behaviour for all one-off events
        # while still being somewhat reasonable for other tasks 
        max_events_per_consumer_heartbeat = environment_common.SKIPPER_CELERY_EVENT_QUEUE_MAX_EVENTS_PER_CONSUMER_HEARTBEAT
        while True:
            with transaction.atomic():
                more_events, sent_count = try_send_events(
                    consumer,
                    proxy_url=environment_common.SKIPPER_CONSUMER_PROXY_URL,
                    max_events=100
                )
                total_sent_count += sent_count
                if not more_events:
                    break
                
            if total_sent_count > max_events_per_consumer_heartbeat:
                # back off, give someone else the chance to go again
                # if no one is there the immediate enqueue ensures we continue
                logger.info(f'backing off after {total_sent_count} events were sent...')
                actual_run_heartbeat_consumers.apply_async(
                    args=[
                        consumer.tenant.id,
                        consumer.id,
                    ],
                    expires=360
                )


@task(name='_3_actual_run_heartbeat', queue='event_queue', ignore_result=True)  # type: ignore
def actual_run_heartbeat_consumers(tenant_id: str, consumer_id: str) -> None:
    _list = Tenant.objects.filter(id=tenant_id)
    if len(_list) != 1:
        logger.warn('did not find tenant with id ' + tenant_id)
        return
    tenant = _list[0]
    queue = get_queue(
        tenant=tenant,
        var_key=str(tenant_id) + '_' + str(tenant.name) + '_' + str(consumer_id),
        queue_base_name='consumer',
        tasks={
            'consumer_heartbeat': consumer_heartbeat
        },
        heartbeat=True,
        at_most_once=True
    )
    with transaction.atomic():
        # make sure the heartbeat task exists
        # this only queues a task if none already exists
        # this might be hacky to enqueue the task here constantly, but it works
        # and we dont end up with duplicates
        queue.enqueue(
            'consumer_heartbeat',
            {
                'consumer_id': str(consumer_id)
            }
        )
    try_run_all(queue)


# run this in celery every x seconds to wake up the event queue beat
@task(name="_3_wake_up_heartbeat_consumers", queue='event_queue', ignore_result=True)   # type: ignore
def wake_up_heartbeat_consumers() -> None:
    dataseries_consumers = list(DataSeries_Consumer.objects.all().filter(
        tenant__deleted_at__isnull=True,
        tenant__id__isnull=False
    ))
    shuffle(dataseries_consumers)
    for dataseries_consumer in dataseries_consumers:
        actual_run_heartbeat_consumers.apply_async(
            args=[
                dataseries_consumer.tenant_id,
                dataseries_consumer.consumer_id,
            ],
            expires=360
        )
