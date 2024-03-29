# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


export DOCKER_CLI_EXPERIMENTAL=enabled
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || exit 1
docker buildx rm armv7-builder || echo "no armv7-builder found... ignoring remove command"
docker buildx create --name armv7-builder --driver docker-container --use || exit 1
docker buildx inspect --bootstrap || exit 1