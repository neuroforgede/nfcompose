#!/bin/bash

cd ..
DEV_NETWORK_NAME=$(whoami)_integration_dev_nfcompose COMPOSE_PROJECT_NAME=$(whoami)_integration_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) bash destroy.sh