# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


SKIPPER_CONTAINER_TYPE=CELERY exec python3 -m pipenv run celery -A skipper \
    beat \
    --pidfile=/neuroforge/skipper/celery.pid \
    --loglevel=INFO
