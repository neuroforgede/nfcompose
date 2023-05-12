#!/bin/bash
cd skipper
if [[ "$BUILD_SOURCEBRANCH" == "refs/heads/production" ]]; then
    echo "latestProduction"
    exit 0
else
    exec python3 -c 'import buildinfo.version; print(buildinfo.version.version_string)'
fi