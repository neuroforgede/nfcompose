#!/bin/bash

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        cd $CUR_DIR
        # bash ci_destroy.sh || echo "failed to run cleanup on error"
        exit 1
    fi
}

# check if we have a proper docker project name set
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    echo "no COMPOSE_PROJECT_NAME set. exiting..."
    exit 1
fi

CUR_DIR=$(pwd)

FAILED='no'

docker run --rm --network "${COMPOSE_PROJECT_NAME}_nfcompose" -v "$(pwd):/client" --rm python:3.11 bash -c 'cp -r /client /tests && cd /tests && rm -rf venv && bash create_venv.sh && source venv/bin/activate && bash install_dev_dependencies.sh && exec bash test.sh'
check_result "integration tests failed"
# END testing section

# cd $CUR_DIR
# bash ci_destroy.sh
# check_result "failed to run ci_destroy.sh"

# if [ "$FAILED" == 'yes' ]; then
#     echo "failed to run integration tests."
#     exit 1
# else
#     echo "ran integration tests successfully."
# fi


