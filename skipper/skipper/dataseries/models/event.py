# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import logging
import traceback
from uuid import UUID
from opentelemetry import trace  # type: ignore

import datetime
import requests
from django.db import transaction
from django.db.models import IntegerField, CharField, Model, DateTimeField, CASCADE, Q, ForeignKey, DO_NOTHING, \
    TextField, BigAutoField, BigIntegerField
from django.utils import timezone
from django_multitenant.fields import TenantForeignKey  # type: ignore
from django_multitenant.mixins import TenantModelMixin  # type: ignore
from django_multitenant.models import TenantManager  # type: ignore
from enum import Enum
from typing import Iterable, Tuple, Dict, Any, Union, Optional, cast, Pattern, Callable

from skipper.core.models import fields
from skipper.core.models.tenant import get_tenant_model, Tenant
from skipper.core.validators import json_dict_str_str, json_dict
from skipper.dataseries.models.metamodel.consumer import Consumer, ConsumerHealthState

logger = logging.getLogger(__name__)

import string
import secrets
import re
from urllib.parse import urlsplit


def fake_agent() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))


class ConsumerEventState(Enum):
    # default should always be the first, so DRF displays it by default in the UI
    NEW = "NEW"
    RETRY = 'RETRY'
    FAILED = 'FAILED'
    SUCCESS = 'SUCCESS'

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


class ConsumerEventType(Enum):
    # default should always be the first, so DRF displays it by default in the UI
    DATA_POINT_CHANGED = "DATA_POINT_CHANGED"
    DATA_POINT_DELETED = "DATA_POINT_DELETED"
    DATA_SERIES_TRUNCATED = "DATA_SERIES_TRUNCATED"

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


class ConsumerEvent(TenantModelMixin, Model):  # type: ignore
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING)

    id = BigAutoField(primary_key=True)
    # we have to order by point_in_time date to try our best for proper order when
    # sending events
    point_in_time = DateTimeField(auto_now_add=False, db_index=True)
    sub_clock = BigIntegerField(null=True)
    last_updated_at = DateTimeField(auto_now=True, db_index=False)

    # how many backoff cycles did we go through
    backoff_cycles = IntegerField(null=False, default=0)
    # how often did we retry in the current cycle
    retries_in_cycle = IntegerField(null=False, default=0)
    # when to first consider this event when handling.
    # stupid implementation, just query all and check first
    # smarter-ish implementation, use FIRST_VALUE query
    handle_at = DateTimeField(null=True, blank=True)

    retries = IntegerField(null=False, default=0)

    # TODO: we should partition on the consumer, then we can simply drop a partition when we want to bulk deletion
    # we dont want to cascade as that is a costly operation, regular cleanup will do the job just fine
    consumer = TenantForeignKey(Consumer, on_delete=DO_NOTHING)
    payload = fields.empty_dict_not_blank_json_field(validators=[json_dict])

    state = CharField(max_length=100, null=False, choices=ConsumerEventState.choices(), db_index=True)
    event_type = CharField(max_length=100, null=False, choices=ConsumerEventType.choices(), db_index=False)

    response = TextField(null=True, blank=True)
    response_headers = fields.optional_empty_dict_not_blank_json_field(
        validators=[json_dict_str_str]
    )
    status_code = IntegerField(null=True, blank=True)
    exception = TextField(null=True, blank=True)

    objects: TenantManager = TenantManager()

    @property
    def tenant_field(self) -> str:
        return 'tenant_id'

    class Meta:
        db_table = '_3_consumer_event'
  

def truncate_events(
    tenant: Tenant,
    data_series_id: Union[str, UUID],
) -> None:
    for consumer in Consumer.objects.filter(
        tenant=tenant,
        dataseries_consumer__data_series__id=data_series_id
    ).all():
        ConsumerEvent.objects.filter(
            tenant=tenant,
            consumer=consumer
        ).delete()


def data_point_event(
        tenant: Tenant,
        data_series_id: Union[str, UUID],
        point_in_time: datetime.datetime,
        sub_clock: int,
        payload: Dict[str, Any],
        event_type: ConsumerEventType
) -> None:
    for consumer in Consumer.objects.filter(
        tenant=tenant,
        dataseries_consumer__data_series__id=data_series_id
    ).all():
        ConsumerEvent.objects.create(
            point_in_time=point_in_time,
            sub_clock=sub_clock,
            tenant=tenant,
            consumer=consumer,
            payload=payload,
            retries=0,
            state=ConsumerEventState.NEW.value,
            event_type=event_type.value
        )


RESPONSE_HEADERS_ALLOW_LIST = {
    'Content-Disposition',
    'Content-Encoding',
    'Content-Language',
    'Content-Length',
    'Content-Location',
    'Content-Range',
    'Content-Type',
}
MAX_RESPONSE_LENGTH = 1024
TRUSTED_HOSTS_REGEX = [
    '.*.local:[0-9]+'
]
TRUSTED_HOSTS_PATTERNS_COMPILED: Iterable[Pattern[str]] = list(re.compile(regex) for regex in TRUSTED_HOSTS_REGEX)


def is_trusted_consumer_target(target: str) -> bool:
    return any(pattern.fullmatch(target) for pattern in TRUSTED_HOSTS_PATTERNS_COMPILED)


def sanitize_response_untrusted(x: str) -> str:
    if len(x) > MAX_RESPONSE_LENGTH:
        return f'{x[0:MAX_RESPONSE_LENGTH]}...'
    return x


def sanitize_headers_untrusted(x: Dict[str, str]) -> Dict[str, str]:
    return dict({k: v for k, v in x.items() if k in RESPONSE_HEADERS_ALLOW_LIST})


def identity(x: Any) -> Any:
    return x


def try_send_events(
    consumer: Consumer,
    proxy_url: Optional[str],
    log_errors: bool = True,
    max_events: Optional[int] = None
) -> Tuple[bool, int]:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span('skipper.dataseries.models.event.try_send_events', attributes={
        "skipper.dataseries.consumer": str(consumer.id),
        "skipper.core.tenant": str(consumer.tenant.name)
    }):
        _split_target_url = urlsplit(consumer.target)
        sanitize_response: Callable[[str], str]
        sanitize_headers: Callable[[Dict[str, str]], Dict[str, str]]
        if not is_trusted_consumer_target(_split_target_url.netloc):
            sanitize_response = sanitize_response_untrusted
            sanitize_headers = sanitize_headers_untrusted
        else:
            sanitize_response = identity
            sanitize_headers = identity

        health = consumer.health
        event: ConsumerEvent
        cnt = 0
        more_events: bool = False
        tenant_name = str(consumer.tenant.name)
        
        _qs = ConsumerEvent.objects.filter(
            ~Q(state__in=[ConsumerEventState.FAILED.value, ConsumerEventState.SUCCESS.value]),
            consumer=consumer
        ).select_for_update().order_by('point_in_time', 'id', 'sub_clock').all()
        _iterable: Iterable[ConsumerEvent]

        if max_events is None:
            _iterable = _qs.iterator()
        else:
            # one more so we can check if there are any left at the end
            _iterable = _qs[:(max_events + 1)]
        
        for event in _iterable:
            if max_events is not None and cnt >= max_events:
                # don't handle this one, but return True as there are more events to process
                more_events = True
                break
            cnt += 1
            failed = False
            with transaction.atomic():
                if event.handle_at is not None:
                    if event.handle_at > timezone.now():
                        # we are not allowed to handle this event just yet
                        break
                    elif event.retries_in_cycle >= consumer.retry_backoff_every:
                        # we are starting a new cycle, so reset the counter
                        # and continue normal handling
                        event.backoff_cycles = event.backoff_cycles + 1
                        event.retries_in_cycle = 0
                url = consumer.target
                body: Dict[str, Any] = {
                    'point_in_time': event.point_in_time.isoformat(),
                    'event_type': event.event_type,
                    'tenant': tenant_name,
                    'payload': event.payload
                }
                if event.sub_clock:
                    body['sub_clock'] = event.sub_clock
                headers = consumer.headers
                if headers is None:
                    headers = {}  # type: ignore
                if 'User-Agent' not in headers:
                    headers['User-Agent'] = fake_agent()
                try:
                    _resp: Optional[requests.Response] = None
                    if proxy_url is not None and proxy_url != '':
                        _resp = requests.post(
                            proxy_url,
                            headers={
                                **headers,
                                'x-skipper-proxied-host': _split_target_url.hostname,
                                'x-skipper-proxied-url': url,
                            },
                            json=body,
                            timeout=consumer.timeout,
                            allow_redirects=False
                        )
                    else:
                        _resp = requests.post(
                            url,
                            headers=headers,
                            json=body,
                            timeout=consumer.timeout,
                            allow_redirects=False
                        )
                    event.response = sanitize_response(_resp.text)
                    event.status_code = _resp.status_code
                    event.response_headers = sanitize_headers(dict(_resp.headers))
                    _resp.raise_for_status()
                    event.exception = None
                    event.state = ConsumerEventState.SUCCESS.value
                    health = ConsumerHealthState.HEALTHY.value
                    logger.info(f'successfully sent message for event with id {event.id} ({event.event_type}) to'
                                f' consumer at {consumer.target}, setting to SUCCESS...')
                except:
                    if _resp is None:
                        event.response = None
                        event.status_code = None
                        event.response_headers = None
                    event.exception = traceback.format_exc()
                    failed = True
                    event.retries = event.retries + 1
                    event.retries_in_cycle = event.retries_in_cycle + 1
                    if event.retries_in_cycle >= consumer.retry_backoff_every:
                        event.handle_at = timezone.now() + consumer.retry_backoff_delay
                    # noinspection PyChainedComparisons
                    if consumer.retry_max > 0 and event.retries > consumer.retry_max:
                        health = ConsumerHealthState.UNHEALTHY.value
                        if log_errors:
                            logger.exception(f'failed to send message to consumer at {consumer.target}, setting to FAILED...')
                        event.state = ConsumerEventState.FAILED.value
                    else:
                        health = ConsumerHealthState.UNHEALTHY.value
                        if log_errors:
                            logger.exception(f'failed to send message to consumer at {consumer.target}, setting to RETRY...')
                        event.state = ConsumerEventState.RETRY.value
                event.save()
            if failed:
                break

        if consumer.health != health:
            consumer.health = health
            consumer.save(update_fields=['health'])

        return more_events, cnt


def delete_old_events(consumer: Consumer, log_errors: bool = True) -> None:
    # delete all events that were successful or failed that originated more than 30 days ago
    ConsumerEvent.objects.filter(
        state__in=[ConsumerEventState.FAILED.value, ConsumerEventState.SUCCESS.value],
        consumer=consumer,
        point_in_time__lte=timezone.now() - timezone.timedelta(days=30)
    ).delete()


def delete_all_events_for_consumer(consumer: Consumer, log_errors: bool = True) -> None:
    # once we partition the event table, we can do this smarter
    ConsumerEvent.objects.filter(
        consumer=consumer
    ).delete()


def hard_delete_consumer(consumer: Consumer, log_errors: bool = True) -> None:
    with transaction.atomic():
        delete_all_events_for_consumer(consumer)
        consumer.hard_delete()


