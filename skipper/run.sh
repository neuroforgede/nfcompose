# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


python3 -m pipenv run python manage.py collectstatic --noinput
python3 -m pipenv run python manage.py migrate
SKIPPER_DEBUG_RUN=true SKIPPER_CONTAINER_TYPE='DJANGO' SKIPPER_DEBUG_LOCAL=true exec python3 -m pipenv run runProduction
