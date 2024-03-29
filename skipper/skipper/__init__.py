# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from __future__ import absolute_import

import os

if os.environ.get('SKIPPER_GUNICORN', 'false') == 'true':
    # python 3.9 and python 3.10 need this to be done as soon as possible
    # also, only do this for gunicorn. Celery workers are still
    # using the sync workers since its simpler
    from psycogreen.gevent import patch_psycopg  # type: ignore
    from gevent import monkey  # type: ignore
    monkey.patch_all()
    patch_psycopg()


# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
