# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


SKIPPER_CONTAINER_TYPE=CELERY exec python3 -m pipenv run celery -A skipper worker --loglevel=info -Q celery,event_queue,event_cleanup,health_check,data_series_cleanup,persist_data,file_registry_cleanup,index_creation,requeue_persist_data
