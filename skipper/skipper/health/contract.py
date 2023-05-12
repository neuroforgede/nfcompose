# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Protocol, Dict

from health_check import exceptions as _exceptions  # type: ignore

# we simply use the same exceptions as the health_check backend so we dont have to
# do any weird re-wrapping of exceptions


HealthCheckException = _exceptions.HealthCheckException
"""
base class for all health check exceptions
"""

ServiceWarning = _exceptions.ServiceWarning
ServiceUnavailable = _exceptions.ServiceUnavailable
ServiceReturnedUnexpectedResult = _exceptions.ServiceReturnedUnexpectedResult


class HealthCheck(Protocol):
    def __call__(self) -> None: ...


_health_checks: Dict[str, HealthCheck] = dict()


def register_health_check(key: str, check: HealthCheck) -> None:
    _health_checks[key] = check
