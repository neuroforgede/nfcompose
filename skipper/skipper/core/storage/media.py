# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.utils.deconstruct import deconstructible
from storages.utils import setting  # type: ignore

from skipper.core.storage.private_public import PrivatePublicS3Boto3Storage


@deconstructible
class S3Boto3MediaStorage(PrivatePublicS3Boto3Storage):  # type: ignore
    bucket_name = setting('NF_AWS_STORAGE_BUCKET_NAME_MEDIA')
    access_key = setting('SKIPPER_S3_MEDIA_ACCESS_KEY_ID')
    secret_key = setting('SKIPPER_S3_MEDIA_SECRET_ACCESS_KEY')
    endpoint_url = setting('SKIPPER_S3_MEDIA_ENDPOINT_URL')
    external_endpoint_url = setting('SKIPPER_S3_MEDIA_EXTERNAL_ENDPOINT_URL')
    region_name = setting('SKIPPER_S3_MEDIA_REGION_NAME')
    addressing_style = setting('SKIPPER_S3_MEDIA_ADDRESSING_STYLE')
