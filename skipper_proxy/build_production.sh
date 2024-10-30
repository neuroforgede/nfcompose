#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

docker build $ARGS -f Dockerfile \
    -t ghcr.io/neuroforgede/nfcompose-skipper-proxy:${BUILD_NF_COMPOSE_DOCKER_TAG} \
    .
check_result "failed build"

docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $(pwd)/.trivyignore:/.trivyignore \
    -e TRIVY_DB_REPOSITORY=ghcr.io/aquasecurity/trivy-db,public.ecr.aws/aquasecurity/trivy-db \
    aquasec/trivy \
    image \
    --scanners vuln \
    --ignore-unfixed \
    --exit-code 1 \
    ghcr.io/neuroforgede/nfcompose-skipper-proxy:${BUILD_NF_COMPOSE_DOCKER_TAG}
check_result "failed trivy check"