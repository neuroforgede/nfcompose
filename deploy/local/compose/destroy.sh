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

if [ "$DELETE_ORPHANS" == "yes" ]; then
    docker-compose down -v --remove-orphans
    check_result "failed to run docker-compose down --remove-orphans"
else
    docker-compose down -v
    check_result "failed to run docker-compose down"
fi