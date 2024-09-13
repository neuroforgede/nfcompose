#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# [2019] - [2021] © NeuroForge GmbH & Co. KG
# All rights reserved

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

function retry {
  local n=1
  local max=10
  local delay=15
  while true; do
    "$@" && break || {
      if [[ $n -lt $max ]]; then
        ((n++))
        echo "Command failed. Attempt $n/$max..."
        sleep $delay;
      else
        echo "The command has failed after $n attempts."
        return 1
      fi
    }
  done
}

function _ensure_bucket {
  BUCKET_EXISTS=$(docker compose exec -T awscli bash -c "INTERNAL_DOMAIN_SUFFIX=${INTERNAL_DOMAIN_SUFFIX:-test.local} AWS_ACCESS_KEY_ID=skipper-test AWS_SECRET_ACCESS_KEY=WMH37f3R8RZyN2CMycWGV3EwuMpxGKhG8NBKaswD6hfFPUrmhg9b6PjfyD8RW4AV3JuRLDTa8JRvTWRYASs5xbwB9qHyTW7BZ6V59FPTytb7jvZ4VsnmbrY4WRSVCS9C aws --region eu-west-1 --endpoint-url http://nfcomposes3.${INTERNAL_DOMAIN_SUFFIX:-test.local}:6044 s3api head-bucket --bucket $1 2>&1")

  if [ -z "$BUCKET_EXISTS" ]; then
    echo "Bucket $1 already exists"
  else
    echo "Bucket $1 does not already exist."
    docker compose exec -T awscli bash -c "INTERNAL_DOMAIN_SUFFIX=${INTERNAL_DOMAIN_SUFFIX:-test.local} AWS_ACCESS_KEY_ID=skipper-test AWS_SECRET_ACCESS_KEY=WMH37f3R8RZyN2CMycWGV3EwuMpxGKhG8NBKaswD6hfFPUrmhg9b6PjfyD8RW4AV3JuRLDTa8JRvTWRYASs5xbwB9qHyTW7BZ6V59FPTytb7jvZ4VsnmbrY4WRSVCS9C aws --region eu-west-1 --endpoint-url http://nfcomposes3.${INTERNAL_DOMAIN_SUFFIX:-test.local}:6044 s3 mb s3://$1"
    if [ $? -ne 0 ]; then
        echo "failed to create bucket $1"
        return 1
    fi
  fi
}

function ensure_bucket {
  retry _ensure_bucket $1
}

if [ "$NFCOMPOSE_SETUP_SKIP_PULL" == "yes" ]; then
    echo "skipping nfcompose image pull."
else
    docker compose -f docker compose.yml pull
    check_result "failed to pull docker images"
fi

docker compose -f docker compose.yml up -d
check_result "failed to create docker compose services"

USER_STRING='"admin"'
PASSWORD_STRING='"admin"'
EMAIL_STRING='"admin@localhost.de"'

echo "migrating nfcompose database..."
docker compose exec -T nfcomposeskipper bash -c 'cd /neuroforge/skipper && exec python manage.py migrate' # && exit 1
check_result "failed to migrate database"

echo "adding admin:admin user to nfcompose..."
docker compose exec -T nfcomposeskipper bash -c "cd /neuroforge/skipper && exec python manage.py shell -c 'from django.contrib.auth.models import User; \
User.objects.filter(username=${USER_STRING}).exists() or User.objects.create_superuser(${USER_STRING}, ${EMAIL_STRING}, ${PASSWORD_STRING})
'"
check_result "failed to create admin:admin user"

cat nf_setup.py | docker compose exec -T nfcomposeskipper bash -c "cd /neuroforge/skipper && exec python manage.py shell"
check_result "failed to run test user setup"

ensure_bucket 'skipper-static'
check_result "failed to create skipper-static s3 bucket"

ensure_bucket 'skipper-media'
check_result "failed to create skipper-media s3 bucket"

echo "collecting static files for nfcompose..."
docker compose exec -T nfcomposeskipper bash -c 'cd /neuroforge/skipper && exec python manage.py collectstatic --noinput'
check_result "failed to collect static files"

echo "setting up anonymous policies for skipper-static bucket"
docker compose run --entrypoint /bin/sh --rm minio_client /minio_client_scripts/setup_anonymous_user.sh
check_result "failed to set policies for skipper-static bucket"