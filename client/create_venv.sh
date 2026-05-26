#!/bin/bash

# use the supported system Python from the current environment
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else "compose_client requires Python 3.9+")'
python3 -m venv venv
