# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from __future__ import absolute_import
import os
from typing import Union, Any
from celery import Celery  # type: ignore
from celery.schedules import crontab  # type: ignore
from django.conf import settings

# set the default Django settings module for the 'celery' program.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skipper.settings')
app = Celery('skipper', result_backend=settings.CELERY_RESULT_BACKEND)


def int_or_crontab(input: Any, key: str) -> Union[int, crontab]:
    if isinstance(input, int):
        return input
    if isinstance(input, crontab):
        return input
    try:  # attempt to interpret input as positive int
        out = int(input)
        if out <= 0:
            raise ValueError()  # not positive, break out of try block
        return out
    except BaseException:
        pass  # try the next option
    try:  # attempt to interpret input as crontab
        if isinstance(input, str) and len(input.split()) >= 5:
            parts = input.split()
        
            minute, hour, day_of_month, month, day_of_week = parts[:5]
            
            return crontab(
                minute=minute,
                hour=hour,
                day_of_week=day_of_week,
                day_of_month=day_of_month,
                month_of_year=month
            )
        else:
            raise ValueError()  # not a crontab, break out of try block
    except BaseException:
        # both failed, now raise
        raise ValueError(f'{key} was passed in a bad format. '
                         'Either pass a positive integer or a string '
                         f'in crontab(5) format. The passed value was {input}')


# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.worker_prefetch_multiplier = 1
app.conf.beat_schedule = {
    'event-queue-heartbeat': {
        'task': '_3_wake_up_heartbeat_consumers',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_EVENT_QUEUE_HEARTBEAT_SCHEDULE', 10),
            'SKIPPER_CELERY_EVENT_QUEUE_HEARTBEAT_SCHEDULE'
        ),
        'options': {
            'queue': 'event_queue',
            'expires': int_or_crontab(
                getattr(settings, 'SKIPPER_CELERY_EVENT_QUEUE_HEARTBEAT_SCHEDULE', 10),
                'SKIPPER_CELERY_EVENT_QUEUE_HEARTBEAT_SCHEDULE'
            )
        }
    },
    'event-cleanup-heartbeat': {
        'task': '_3_wake_up_consumer_cleanup',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_EVENT_QUEUE_CLEANUP_SCHEDULE', crontab(hour=1)),
            'SKIPPER_CELERY_EVENT_QUEUE_CLEANUP_SCHEDULE'
        ),
        'options': {
            'queue': 'event_cleanup'
        }
    },
    'data_series-history-cleanup-heartbeat': {
        'task': '_3_wake_up_data_series_history_cleanup',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_DATA_SERIES_HISTORY_CLEANUP_SCHEDULE', crontab(hour=1)),
            'SKIPPER_CELERY_DATA_SERIES_HISTORY_CLEANUP_SCHEDULE'
        ),
        'options': {
            'queue': 'data_series_cleanup'
        }
    },
    'file-registry-cleanup-heartbeat': {
        'task': '_3_wake_up_file_registry_cleanup',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_SCHEDULE', crontab(hour=1)),
            'SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_SCHEDULE'
        ),
        'options': {
            'queue': 'file_registry_cleanup'
        }
    },
    'data_series-meta-model-cleanup-heartbeat': {
        'task': '_3_wake_up_data_series_meta_model_cleanup',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_DATA_SERIES_META_MODEL_CLEANUP_SCHEDULE', crontab(hour=1)),
            'SKIPPER_CELERY_DATA_SERIES_META_MODEL_CLEANUP_SCHEDULE'
        ),
        'options': {
            'queue': 'data_series_cleanup'
        }
    },
    'data_series-requeue-persist-data-point-chunk-heartbeat': {
        'task': '_3_wake_up_requeue_persist_data_point_chunk',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_PERSIST_DATA_POINT_CHUNK_REQUEUE_SCHEDULE', 60 * 30),
            'SKIPPER_CELERY_PERSIST_DATA_POINT_CHUNK_REQUEUE_SCHEDULE'
        ),
        'options': {
            'queue': 'requeue_persist_data',
            'expires': int_or_crontab(
                getattr(settings, 'SKIPPER_CELERY_PERSIST_DATA_POINT_CHUNK_REQUEUE_SCHEDULE', 60 * 30),
                'SKIPPER_CELERY_PERSIST_DATA_POINT_CHUNK_REQUEUE_SCHEDULE'
            )
        }
    },
    'health-check-heartbeat': {
        'task': '_5_run_health_checks',
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_HEALTH_CHECK_HEARTBEAT_SCHEDULE', 30),
            'SKIPPER_CELERY_HEALTH_CHECK_HEARTBEAT_SCHEDULE'
        ),
        'options': {
            'queue': 'health_check',
            'expires': int_or_crontab(
                getattr(settings, 'SKIPPER_CELERY_HEALTH_CHECK_HEARTBEAT_SCHEDULE', 30),
                'SKIPPER_CELERY_HEALTH_CHECK_HEARTBEAT_SCHEDULE'
            ),
        }
    },
    'common-cleanup-outstanding-tokens-heartbeat': {
        'task': '_common_cleanup_outstanding_tokens',
        # every hour
        'schedule': int_or_crontab(
            getattr(settings, 'SKIPPER_CELERY_OUTSTANDING_TOKENS_CLEANUP_SCHEDULE', 60 * 60),
            'SKIPPER_CELERY_OUTSTANDING_TOKENS_CLEANUP_SCHEDULE'
        ),
        'options': {
            'queue': 'event_cleanup',
            'expires': int_or_crontab(
                getattr(settings, 'SKIPPER_CELERY_OUTSTANDING_TOKENS_CLEANUP_SCHEDULE', 60 * 60),
                'SKIPPER_CELERY_OUTSTANDING_TOKENS_CLEANUP_SCHEDULE'
            )
        }
    },
}
