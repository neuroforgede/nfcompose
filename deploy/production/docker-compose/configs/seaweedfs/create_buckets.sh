#!/bin/bash

# NeuroForge GmbH & Co. KG confidential
#
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
  BUCKET_EXISTS=$(aws --region eu-west-1 --endpoint-url http://nfcomposes3.local:8000 s3api head-bucket --bucket $1 2>&1)

  if [ -z "$BUCKET_EXISTS" ]; then
    echo "Bucket $1 already exists"
  else
    echo "Bucket $1 does not already exist."
    aws --region eu-west-1 --endpoint-url http://nfcomposes3.local:8000 s3 mb s3://$1
    if [ $? -ne 0 ]; then
        echo "failed to create bucket $1"
        return 1
    fi
  fi
}

function ensure_bucket {
  retry _ensure_bucket $1
}

ensure_bucket 'skipper-static'
check_result "failed to create skipper-static s3 bucket"

ensure_bucket 'skipper-media'
check_result "failed to create skipper-media s3 bucket"