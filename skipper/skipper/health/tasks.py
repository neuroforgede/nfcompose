# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import logging
import time

from skipper.core.celery import task  # type: ignore
from django.utils import timezone
from typing import List, Any, Optional, Dict

from skipper.health import contract
from skipper.health.models import SubSystemHealthStatus, SubSystemHealth

logger = logging.getLogger(__name__)


def pretty_errors(errors: List[contract.HealthCheckException]) -> List[Dict[str, Any]]:
    ret: List[Dict[str, Any]] = []
    for error in errors:
        obj: Dict[str, Any] = {
            'message_type': str(error.message_type)
        }
        if isinstance(error.message, dict) or isinstance(error.message, list):
            obj['error_payload'] = error.message
        else:
            obj['error_payload'] = str(error.message)
        ret.append(obj)
    return ret


def convert_error(errors: List[contract.HealthCheckException], error: Any, cause: Optional[Any] = None) -> None:
    if isinstance(error, contract.HealthCheckException):
        pass
    elif isinstance(error, str):
        msg = error
        error = contract.HealthCheckException(msg)
    else:
        msg = 'unknown error'
        error = contract.HealthCheckException(msg)
    if isinstance(cause, BaseException):
        logger.exception(str(error))
    else:
        logger.error(str(error))
    errors.append(error)


def sub_system_health(key: str) -> SubSystemHealth:
    if not SubSystemHealth.objects.filter(key=key).exists():
        SubSystemHealth.objects.create(
            key=key
        )
    return SubSystemHealth.objects.get(key=key)


# noinspection PyProtectedMember
@task(name='_5_run_health_checks', queue='health_check', ignore_result=True)  # type: ignore
def run_health_checks() -> None:
    for key, check in contract._health_checks.items():
        start = time.perf_counter()
        time_taken: float
        errors: List[contract.HealthCheckException] = []
        _status: SubSystemHealthStatus = SubSystemHealthStatus.UNKNOWN
        now = timezone.now()
        # noinspection PyBroadException
        try:

            check()
            _status = SubSystemHealthStatus.HEALTHY
        except contract.HealthCheckException as e:
            _status = SubSystemHealthStatus.UNHEALTHY
            errors.append(e)
        except:
            _status = SubSystemHealthStatus.UNKNOWN
            logger.exception("Unexpected Error!")
        finally:
            time_taken = time.perf_counter() - start

        health_obj = sub_system_health(key=key)
        health_obj.health = _status.value
        health_obj.last_errors = pretty_errors(errors)
        health_obj.time_taken = time_taken
        health_obj.last_check = now
        health_obj.save()
