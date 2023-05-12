#!/bin/bash

cd ../deploy
DEV_NETWORK_NAME=$(whoami)_client_dev_nfcompose COMPOSE_PROJECT_NAME=$(whoami)_client_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) bash destroy.sh