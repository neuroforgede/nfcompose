#!/bin/bash

COMPOSE_PROJECT_NAME=$(whoami)_client_dev CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker compose exec client_dev bash