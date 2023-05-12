# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.utils.deconstruct import deconstructible
from skipper.core.storage.private_public import PrivatePublicS3Boto3Storage
from storages.utils import setting  # type: ignore

@deconstructible
class S3Boto3StaticStorage(PrivatePublicS3Boto3Storage):  # type: ignore
    bucket_name = setting('NF_AWS_STORAGE_BUCKET_NAME_STATIC')
    querystring_auth = setting('NF_AWS_QUERYSTRING_AUTH_STATIC')
