#!/bin/sh

# s3 username:
S3_IDENTITY_ACCESSKEY="skipper-test"
# s3 password
S3_IDENTITY_SECRETKEY="WMH37f3R8RZyN2CMycWGV3EwuMpxGKhG8NBKaswD6hfFPUrmhg9b6PjfyD8RW4AV3JuRLDTa8JRvTWRYASs5xbwB9qHyTW7BZ6V59FPTytb7jvZ4VsnmbrY4WRSVCS9C"
# s3 url
S3_URL="http://nfcomposes3.${INTERNAL_DOMAIN_SUFFIX:-test.local}:8000"

# set minio alias:
mc alias set nfcomposes3 $S3_URL $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

# create skipper-test user with policies:
mc admin user add nfcomposes3 $S3_IDENTITY_ACCESSKEY $S3_IDENTITY_SECRETKEY
mc admin policy set nfcomposes3 consoleAdmin,diagnostics,readwrite user=$S3_IDENTITY_ACCESSKEY
