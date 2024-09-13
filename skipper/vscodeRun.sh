#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) exec docker compose exec neuroforge_skipper_base_dev bash -c 'cd /neuroforge/skipper && exec bash run.sh'
