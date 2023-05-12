#!/bin/bash
source venv/bin/activate || echo 'not using a venv'
bash typecheck.sh || exit 1
exec pytest
