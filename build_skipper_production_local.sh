#!/bin/bash
export SKIPPER_BUILD_TEST_CONTAINER="$(whoami)_skipper_neuroforge_skipper_base_dev_1"

cd skipper && bash build_production.sh || exit 1
