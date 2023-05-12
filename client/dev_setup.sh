#!/bin/bash

CUR_DIR=$(pwd)

cd ../deploy
COMPOSE_PROJECT_NAME=$(whoami)_client_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) bash setup.sh

cd $CUR_DIR
LOCAL_SKIPPER_DEV_NETWORK_NAME=$(whoami)_skipper_cephalopod DEV_NETWORK_NAME=$(whoami)_client_dev_nfcompose COMPOSE_PROJECT_NAME=$(whoami)_client_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose up -d --build