#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG
# All rights reserved

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

if [ -z "$COMPOSE_PROJECT_NAME" ]; then
    export COMPOSE_PROJECT_NAME="playground"
fi

bash setup.sh
check_result "failed to setup nf compose instance"

cd dev_frontend_proxy
bash setup.sh
check_result "failed to setup frontend proxy"