#!/bin/bash

if [ -z "$COMPOSE_PROJECT_NAME" ]; then
        echo "no project name was set, \$COMPOSE_PROJECT_NAME variable is needed to connect to network"
        exit 1
fi  

set -a
docker-compose down