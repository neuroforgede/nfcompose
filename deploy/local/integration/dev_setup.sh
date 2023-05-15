#!/bin/bash

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

CUR_DIR=$(pwd)

cd ..
COMPOSE_PROJECT_NAME=$(whoami)_integration_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) bash setup.sh
check_result "failed to run setup.sh"

cd $CUR_DIR
DEV_NETWORK_NAME=$(whoami)_integration_dev_nfcompose COMPOSE_PROJECT_NAME=$(whoami)_integration_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose up -d --build
check_result "failed to run docker setup"