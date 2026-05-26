#!/bin/bash
python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else "compose_client development environment requires Python 3.9+")'
python -m pip install -e .[dev]
