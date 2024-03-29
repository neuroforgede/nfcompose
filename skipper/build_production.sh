#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


if [[ "$BUILD_SOURCEBRANCH" == "refs/heads/production" ]]; then
  exec python3 build.py \
    build \
    --imageName ghcr.io/neuroforgede/nfcompose-skipper \
    --buildBase \
    --productionDockerTag true
else
  exec python3 build.py \
    build \
    --imageName ghcr.io/neuroforgede/nfcompose-skipper \
    --buildBase
fi
