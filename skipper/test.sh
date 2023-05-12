#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


SKIPPER_TESTING=true SKIPPER_CELERY_TESTING=true python3 -m pipenv run python manage.py test --no-input --buffer --parallel -v 3
