# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.utils import timezone
from django_multitenant.utils import set_current_tenant  # type: ignore

from skipper.dataseries.models import BulkInsertTaskData
from skipper.dataseries.models.metamodel.consumer import DataSeries_Consumer, Consumer, ConsumerHealthState
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime
from skipper.health import contract


def consumer_healthcheck() -> None:
    unhealthy_consumers = []
    for dataseries_consumer in (
            DataSeries_Consumer
            .objects
            .filter(
                data_series__deleted_at__isnull=True,
                consumer__deleted_at__isnull=True
            ).all()
    ):
        consumer: Consumer = dataseries_consumer.consumer
        data_series: DataSeries = dataseries_consumer.data_series
        if consumer.health == ConsumerHealthState.UNHEALTHY.value:
            unhealthy_consumers.append(f'Tenant - {consumer.tenant.name}, '
                                       f'DataSeries={data_series.external_id}, '
                                       f'Consumer={dataseries_consumer.external_id}, '
                                       f'target={consumer.target} is unhealthy')
    if len(unhealthy_consumers):
        raise contract.ServiceWarning(unhealthy_consumers)


def task_data_health_check() -> None:
    set_current_tenant(None)
    if BulkInsertTaskData.objects.filter(
        point_in_time__lt=dbtime.now() - timezone.timedelta(days=1)
    ).order_by('id').exists():
        raise contract.ServiceWarning('database contains data of tasks that have been in the queue for longer than one day')


def register_health_checks() -> None:
    contract.register_health_check('dataseries.event.consumer', consumer_healthcheck)
    contract.register_health_check('dataseries.datapoint.async', task_data_health_check)

