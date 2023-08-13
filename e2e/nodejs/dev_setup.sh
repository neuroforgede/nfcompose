#!/bin/bash

CUR_DIR=$(pwd)

cd ../../deploy/local
COMPOSE_PROJECT_NAME=$(whoami)_nodejs_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) bash setup.sh

cd $CUR_DIR
LOCAL_SKIPPER_DEV_NETWORK_NAME=$(whoami)_skipper_cephalopod DEV_NETWORK_NAME=$(whoami)_nodejs_dev_nfcompose COMPOSE_PROJECT_NAME=$(whoami)_nodejs_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose up -d --build