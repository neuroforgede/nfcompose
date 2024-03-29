# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.db import transaction
from django.utils import timezone
from django_multitenant.utils import set_current_tenant  # type: ignore

from skipper.core.celery import task
from skipper.core.models.tenant import Tenant
from skipper.dataseries.models import delete_old_events
from skipper.dataseries.models.metamodel.consumer import Consumer, DataSeries_Consumer
from skipper.dataseries.models.metamodel.data_series import DataSeries, ExtraConfigParameters
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage import actions


@task(name='_3_actual_consumer_event_cleanup', queue='event_cleanup', ignore_result=True)  # type: ignore
def actual_consumer_event_cleanup(consumer_id: str) -> None:
    set_current_tenant(None)
    with transaction.atomic():
        _list = Consumer.all_objects.filter(
            id=consumer_id
        )
        if len(_list) != 1:
            return
        consumer = _list[0]
        delete_old_events(consumer)


@task(name="_3_wake_up_consumer_cleanup", queue='event_cleanup', ignore_result=True)  # type: ignore
def wake_up_consumer_cleanup() -> None:
    set_current_tenant(None)
    # cleanup all consumers, even the ones that are deleted
    # also dont filter for deleted tenant here therefore
    for dataseries_consumer in DataSeries_Consumer.all_objects.all():
        actual_consumer_event_cleanup.delay(
            dataseries_consumer.consumer_id
        )


@task(name="_3_wake_up_data_series_history_cleanup", queue='data_series_cleanup', ignore_result=True)  # type: ignore
def wake_up_data_series_history_cleanup() -> None:
    set_current_tenant(None)
    for data_series in DataSeries.objects.all().filter(
        tenant__deleted_at__isnull=True,
        tenant__id__isnull=False
    ):
        tenant = data_series.tenant
        auto_clean_history_after_days = data_series.get_extra_config_property_value(
            ExtraConfigParameters.auto_clean_history_after_days
        )
        if auto_clean_history_after_days > 0:
            older_than = dbtime.now() - timezone.timedelta(days=auto_clean_history_after_days)
            actions.prune_history(
                tenant_id=str(tenant.id),
                data_series_id=str(data_series.id),
                older_than=str(older_than)
            )


@task(name="_3_wake_up_data_series_meta_model_cleanup", queue='data_series_cleanup', ignore_result=True)  # type: ignore
def wake_up_data_series_meta_model_cleanup() -> None:
    set_current_tenant(None)
    for data_series in DataSeries.objects.all().filter(
        tenant__deleted_at__isnull=True,
        tenant__id__isnull=False
    ):
        tenant = data_series.tenant
        auto_clean_meta_model_after_days = data_series.get_extra_config_property_value(
            ExtraConfigParameters.auto_clean_meta_model_after_days
        )
        if auto_clean_meta_model_after_days > 0:
            older_than = dbtime.now() - timezone.timedelta(days=auto_clean_meta_model_after_days)
            actions.prune_metamodel(
                tenant_id=str(tenant.id),
                data_series_id=str(data_series.id),
                older_than=str(older_than)
            )



# to not have to rely on celery doing so many beats, we can use notifications
# problem: this might produce _a lot_ of events and extra strain on the db
# so maybe regular heartbeat is enough? (and actually safe)
# look into Worker construct from pgq-queue when implementing this!



