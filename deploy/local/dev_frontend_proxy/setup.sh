#!/bin/bash

set -a

if [ -z "$COMPOSE_PROJECT_NAME" ]; then
        echo "no project name was set, \$COMPOSE_PROJECT_NAME variable is needed to connect to network"
        exit 1
fi  

docker compose up -d || exit 1 && echo "error setting up containers"

echo "containers are running, it could take a while until they are properly set up"
echo "Don't forget to add the line '127.0.0.1 nfcompose.test.local' to /etc/hosts"