#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


if [ "${SKIPPER_CONTAINER_TYPE}" == "CELERY" ]; then
  exit 0
elif [ "${SKIPPER_CONTAINER_TYPE}" == "DJANGO" ]; then
  [ $(curl -A 'docker-healthcheck DJANGO' -fail -H 'Host: skipper.local' http://localhost:8000/api/ -o /dev/stderr -w '%{http_code}') -eq 403 ] || exit 1
elif [ "${SKIPPER_CONTAINER_TYPE}" == "DJANGO_INTERNAL" ]; then
  [ $(curl -A 'docker-healthcheck DJANGO_INTERNAL' -fail -H 'Host: skipper.local' http://localhost:8000/api/ -o /dev/stderr -w '%{http_code}') -eq 403 ] || exit 1
else
  exit 0
fi