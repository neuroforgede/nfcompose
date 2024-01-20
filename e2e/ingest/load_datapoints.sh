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

for DATASERIES in ${ALL_DATASERIES[@]}
do
    DATAPOINT_DATA=`cat ./compose/datapoints/${DATASERIES}.json`
    check_result "failed to load ${DATASERIES}.json! Exiting..."

    if [ "$DATAPOINT_DATA" != "[]" ]; then
        echo "found operations: $DATAPOINT_DATA"

        echo "Applying operations now..."

        echo "$DATAPOINT_DATA" | compose_cli push datapoints ${NF_COMPOSE_URL} ${DATASERIES} --compose-user ${NF_COMPOSE_USER} --compose-password ${NF_COMPOSE_PASSWORD}
        check_result 'failed to apply operations! Exiting...'

        echo "success."
    else
        echo "found no operations"
    fi
done