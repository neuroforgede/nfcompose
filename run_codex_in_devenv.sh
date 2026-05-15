#!/bin/bash

set -euo pipefail

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(whoami)_skipper}"

exec docker compose exec neuroforge_skipper_base_dev \
  bash -lc 'cd /workspace/nfcompose && exec codex "$@"' \
  bash "$@"
