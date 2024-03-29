# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from psycogreen.gevent import patch_psycopg  # type: ignore
from gevent import monkey  # type: ignore
import logging
from typing import Any



from skipper import settings

reload = settings.DEBUG


def post_fork(server: Any, worker: Any) -> None:
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    monkey.patch_all()
    server.log.info('gunicorn post_fork: successfully used gevent patch call')
    patch_psycopg()
    server.log.info('gunicorn post_fork: successfully patched psycopg2 to be compatible with gevent')

    from skipper import telemetry

    telemetry.setup_telemetry_django()