#!/bin/bash

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        cd $CUR_DIR
        bash ci_destroy.sh || echo "failed to run cleanup on error"
        exit 1
    fi
}

# check if we have a proper docker project name set
if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    echo "no COMPOSE_PROJECT_NAME set. exiting..."
    exit 1
fi

CUR_DIR=$(pwd)
bash ci_setup.sh
check_result "failed to run ci_setup.sh"

FAILED='no'

# START testing section
HTTP_CODE=$(docker run --rm --network "${COMPOSE_PROJECT_NAME}_nfcompose" --rm python:3.11 bash -c 'exec curl -o /dev/null -w '%{http_code}' -s http://admin:admin@skipper.test.local:8000/api/')
if [ "$HTTP_CODE" == '200' ]; then
    echo "successfully got HTTP 200 from skipper"
else
    echo "got HTTP Code $HTTP_CODE"
    echo "did not get a HTTP 200 response from skipper. failing..."
    FAILED='yes'
fi

docker run --rm --network "${COMPOSE_PROJECT_NAME}_nfcompose" -v "$(pwd):/client" --rm python:3.11 bash -c 'cp -r /client /tests && cd /tests && rm -rf venv && bash create_venv.sh && source venv/bin/activate && bash install_dev_dependencies.sh && exec bash test.sh'
check_result "integration tests failed"
# END testing section

cd $CUR_DIR
bash ci_destroy.sh
check_result "failed to run ci_destroy.sh"

if [ "$FAILED" == 'yes' ]; then
    echo "failed to run integration tests."
    exit 1
else
    echo "ran integration tests successfully."
fi


