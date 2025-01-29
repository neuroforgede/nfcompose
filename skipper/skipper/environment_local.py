# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import os

from typing import TYPE_CHECKING

if (
        os.environ.get('SKIPPER_TESTING', 'false') == 'true'
        or os.environ.get('SKIPPER_DEBUG_LOCAL', 'false') == 'true'
        or os.environ.get('MYPY_RUN', 'false') == 'true'
        or TYPE_CHECKING
):
    os.environ.update({
        'SKIPPER_INSTALLATION_NAME': 'localhost',
        'SKIPPER_DJANGO_SECRET_KEY': 't#oin*ss-y%q9!qh)dl#suaof2cl65e3f#q^m&rvtcznogu3ox',
        'SKIPPER_DOMAIN': 'localhost',
        'SKIPPER_TASK_DASHBOARD_ENABLED': 'true',
        'SKIPPER_OTEL_JAEGER_UI_ENABLED': 'true',
        "SKIPPER_DB_USER": 'cephalopod',
        "SKIPPER_DB": 'cephalopod',
        "SKIPPER_DB_PASSWD": 'cephalopod',
        "SKIPPER_DB_HOSTS": os.getenv('SKIPPER_TESTING_DB_HOST', 'postgres_container_cephalopod'),
        "SKIPPER_DB_PORTS": '5432',
        "SKIPPER_DB_SCHEMA": 'public',
        "SKIPPER_SESSION_INSECURE": "true",
        "SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET": 'QAeV8ESByNqyXNA4bUNMqEVvbhR7B4ftCEWTGM2ujbVtMfuHL7YnjhWUzEaUWDW9',
        "SKIPPER_FEATURE_FLAG_ALL": "true",
        # keep anything that was overridden,
        "SKIPPER_S3_ACCESS_KEY_ID": "OJ7LREVSOMBYFMY9R5TY",
        "SKIPPER_S3_SECRET_ACCESS_KEY": "zkxXzd4V61CLF0PBaRoHzwbdr7ftIqduw0oNK74U",
        "SKIPPER_S3_ENDPOINT_URL": "https://nbg1.your-objectstorage.com",
        "SKIPPER_S3_EXTERNAL_ENDPOINT_URL": 'https://nbg1.your-objectstorage.com',
        "SKIPPER_S3_MEDIA_BUCKET_NAME": "nfcomposedev01-media",
        "SKIPPER_S3_MEDIA_ADDRESSING_STYLE": "virtual",
        "SKIPPER_S3_STATIC_BUCKET_NAME": "nfcomposedev01-static",
        "SKIPPER_S3_STATIC_ADDRESSING_STYLE": "path",
        **os.environ
    })
    # for unit tests
    s3_outside_port = os.getenv('SEAWEEDFS_DEV_OUTSIDE_PORT', '6044')
    AWS_S3_TEST_OUTSIDE_BASE_URL = f'http://localhost:{s3_outside_port}'
