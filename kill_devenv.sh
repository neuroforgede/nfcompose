#!/bin/bash
check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}
if [ -f ".env" ]; then
    echo "detected .env loading it"
    source .env
    check_result "failed to load .env file"
    echo "success"
else
    echo "no .env found, using default"
fi
COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker compose down --volumes
FAILED_DOCKER_COMPOSE_DOWN=$?

rm -rf skipper/venv

if [ $FAILED_DOCKER_COMPOSE_DOWN -ne 0 ]; then
    echo "failed to run docker compose down"
    exit 1
fi