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

function retry {
  local n=1
  local max=3
  local delay=15
  while true; do
    "$@" && break || {
      if [[ $n -lt $max ]]; then
        ((n++))
        echo "Command failed. Attempt $n/$max..."
        sleep $delay;
      else
        echo "WARN: The command has failed after $n attempts. It might be fine if you already have a devenv running on this machine and simply wanted to upgrade."
      fi
    }
  done
}

function _ensure_bucket {
  BUCKET_EXISTS=$(docker-compose exec -T awscli bash -c "AWS_ACCESS_KEY_ID=skipper-test AWS_SECRET_ACCESS_KEY=WMH37f3R8RZyN2CMycWGV3EwuMpxGKhG8NBKaswD6hfFPUrmhg9b6PjfyD8RW4AV3JuRLDTa8JRvTWRYASs5xbwB9qHyTW7BZ6V59FPTytb7jvZ4VsnmbrY4WRSVCS9C aws --region eu-west-1 --endpoint-url http://nfcomposes3:8000 s3api head-bucket --bucket $1 2>&1")

  if [ -z "$BUCKET_EXISTS" ]; then
    echo "Bucket $1 already exists"
  else
    echo "$bucket does not already exist."
    docker-compose exec -T awscli bash -c "AWS_ACCESS_KEY_ID=skipper-test AWS_SECRET_ACCESS_KEY=WMH37f3R8RZyN2CMycWGV3EwuMpxGKhG8NBKaswD6hfFPUrmhg9b6PjfyD8RW4AV3JuRLDTa8JRvTWRYASs5xbwB9qHyTW7BZ6V59FPTytb7jvZ4VsnmbrY4WRSVCS9C aws --region eu-west-1 --endpoint-url http://nfcomposes3:8000 s3 mb s3://$1"
    if [ $? -ne 0 ]; then
        echo "failed to create bucket $1"
        return 1
    fi
  fi
}

function ensure_bucket {
  retry _ensure_bucket $1
}

export COMPOSE_PROJECT_NAME=$(whoami)_skipper

COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose build
check_result "failed to run docker-compose build"

COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose up -d
check_result "failed to run docker-compose up -d"

# installing dependencies for skipper
COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose exec -T neuroforge_skipper_base_dev bash -c 'cd /neuroforge/skipper/ && exec bash create_venv.sh'
check_result "failed to setup venv in skipper"

# running migrations and static collection
COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose exec -T neuroforge_skipper_base_dev bash -c 'cd /neuroforge/skipper/ && exec python3 -m pipenv run python3 manage.py migrate'
check_result "failed to run migrations in skipper"

ensure_bucket 'skipper-static'
check_result "failed to create skipper-static s3 bucket"

ensure_bucket 'skipper-media'
check_result "failed to create skipper-media s3 bucket"

COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose exec -T neuroforge_skipper_base_dev bash -c 'cd /neuroforge/skipper/ && exec python3 -m pipenv run python3 manage.py collectstatic --noinput'
check_result "failed to run collectstatic in skipper"

# setup users
COMPOSE_PROJECT_NAME=$(whoami)_skipper CONTAINER_USER_ID=$(id -u) CONTAINER_GROUP_ID=$(id -g) docker-compose exec -T neuroforge_skipper_base_dev bash -c 'cd /neuroforge/skipper/ && exec bash test_setup.sh'
check_result "failed to run test_setup in skipper"
