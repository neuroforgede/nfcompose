#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}


source venv/bin/activate || echo "not using a venv"
export PYTHONPATH=${PYTHONPATH}:${PWD}

# first step, check licenses
liccheck -s liccheck.ini -l PARANOID -r <(pip freeze)
check_result "failed to run license check"

echo "checking types in compose_client"
mypy compose_client --no-strict-optional \
  --warn-unused-configs \
  --disallow-any-generics \
  --disallow-untyped-calls \
  --disallow-untyped-defs \
  --disallow-incomplete-defs \
  --check-untyped-defs \
  --disallow-untyped-decorators \
  --no-implicit-optional \
  --warn-redundant-casts \
  --warn-return-any \
  --disallow-subclassing-any \
  --strict-equality || exit 1 # --show-traceback

echo "checking types in tests"
mypy tests --no-strict-optional \
  --warn-unused-configs \
  --disallow-any-generics \
  --disallow-untyped-calls \
  --disallow-untyped-defs \
  --disallow-incomplete-defs \
  --check-untyped-defs \
  --disallow-untyped-decorators \
  --no-implicit-optional \
  --warn-redundant-casts \
  --warn-return-any \
  --disallow-subclassing-any \
  --strict-equality || exit 1 # --show-traceback

#--no-implicit-reexport \
# --warn-unused-ignores \
