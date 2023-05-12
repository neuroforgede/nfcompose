#!/bin/bash

cd skipper && bash build_production.sh || exit 1
cd ..
cd skipper_proxy && bash build_production.sh || exit 1
