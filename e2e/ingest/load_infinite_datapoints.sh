#!/bin/bash

ALL_DATASERIES=(
    in_order
)

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

source .env

python3 generate_data.py | compose_cli push datapoints ${NF_COMPOSE_URL} in_order --compose-user ${NF_COMPOSE_USER} --compose-password ${NF_COMPOSE_PASSWORD} --lines --batchsize 1
