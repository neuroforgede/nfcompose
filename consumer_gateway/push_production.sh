#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

docker push ghcr.io/neuroforgede/nfcompose-consumer-gateway:${BUILD_NF_COMPOSE_DOCKER_TAG}
check_result "failed to push ghcr.io/neuroforgede/nfcompose-consumer-gateway:${BUILD_NF_COMPOSE_DOCKER_TAG}"
