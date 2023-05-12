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

export PYTHONPATH=${PYTHONPATH}:${PWD}

_PIPENV_PREFIX='python3 -m pipenv run'
_REQUIREMENTS_STR='python3 -m pipenv requirements'
_MYPY_INCREMENTAL='--no-incremental'
if [ "PRODUCTION_BUILD" == "yes" ]; then
    _PIPENV_PREFIX=''
    _REQUIREMENTS_STR='pip3 freeze'
    _MYPY_INCREMENTAL='--no-incremental'
fi

# first step, check licenses
$_PIPENV_PREFIX liccheck -s liccheck.ini -l PARANOID -r <($_REQUIREMENTS_STR)
check_result "failed license check"

MYPY_RUN=true $_PIPENV_PREFIX mypy skipper --no-strict-optional \
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
  $_MYPY_INCREMENTAL \
  --strict-equality || exit 1 # --show-traceback



#--no-implicit-reexport \
# --warn-unused-ignores \
