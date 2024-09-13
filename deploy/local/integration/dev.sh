#!/bin/bash

COMPOSE_PROJECT_NAME=$(whoami)_integration_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker compose exec integration_tests_dev bash