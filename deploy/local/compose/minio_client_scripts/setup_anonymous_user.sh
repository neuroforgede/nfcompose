#!/bin/sh

# s3 url
S3_URL="http://nfcomposes3.${INTERNAL_DOMAIN_SUFFIX:-test.local}:6044"

# set minio alias:
mc alias set nfcomposes3 $S3_URL $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

# set policies for anonymous:
mc anonymous set download nfcomposes3/skipper-static