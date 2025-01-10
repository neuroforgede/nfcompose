import os
import urllib.parse
from typing import List

from skipper.environment_common import *

MANDATORY_ENV_VARS = {
    "SKIPPER_INSTALLATION_NAME",
    "SKIPPER_DOMAIN",
}

env_var_keys = os.environ.keys()
not_set_vars = MANDATORY_ENV_VARS.difference(env_var_keys)
if len(not_set_vars) > 0:
    raise AssertionError(f'environment variables {str(not_set_vars)} are not set. exiting...')


SKIPPER_FLOW_DEFAULT_NODE_RED_ENABLED = os.environ.get('SKIPPER_FLOW_DEFAULT_NODE_RED_ENABLED', "true") == "true"
SKIPPER_FLOW_DEFAULT_NODE_RED_UPSTREAM = os.environ.get('SKIPPER_FLOW_DEFAULT_NODE_RED_UPSTREAM', "http://nodered.local:1880")
SKIPPER_FLOW_DEFAULT_NODE_RED_INTERNAL_UPSTREAM = os.environ.get('SKIPPER_FLOW_DEFAULT_NODE_RED_UPSTREAM', "http://nodered.local:1880")


SKIPPER_CONTAINER_TYPE = os.environ.get('SKIPPER_CONTAINER_TYPE', 'DJANGO')

SKIPPER_DJANGO_DEBUG = os.environ.get('SKIPPER_DJANGO_DEBUG', 'false') == 'true'
SKIPPER_DEBUG_LOCAL = os.environ.get('SKIPPER_DEBUG_LOCAL', 'false') == 'true'
SKIPPER_DEBUG_RUN = os.environ.get('SKIPPER_DEBUG_RUN', 'false') == 'true'
"""
whether we are running via run.sh (locally)
"""


SKIPPER_GUNICORN_WORKER_CONCURRENCY = int(os.environ.get('SKIPPER_GUNICORN_WORKER_CONCURRENCY', '2'))
SKIPPER_GUNICORN_WORKER_DB_POOL_TIMEOUT = int(os.environ.get('SKIPPER_GUNICORN_WORKER_DB_POOL_TIMEOUT', '10'))

SKIPPER_CELERY_WORKER_CONCURRENCY = int(os.environ.get('SKIPPER_CELERY_WORKER_CONCURRENCY', '20'))
SKIPPER_CELERY_WORKER_DB_POOL_TIMEOUT = int(os.environ.get('SKIPPER_CELERY_WORKER_DB_POOL_TIMEOUT', '60'))

SKIPPER_DOMAIN = os.environ['SKIPPER_DOMAIN']

SKIPPER_SESSION_INSECURE = os.environ.get('SKIPPER_SESSION_INSECURE', 'false') == 'true'

SKIPPER_TESTING = os.environ.get('SKIPPER_TESTING', 'false') == 'true'


SKIPPER_DATA_SERIES_BULK_TASK_SIZE = int(os.environ.get('SKIPPER_DATA_SERIES_BULK_TASK_SIZE', '5000'))
SKIPPER_DATA_SERIES_BULK_BATCH_SIZE = int(os.environ.get('SKIPPER_DATA_SERIES_BULK_BATCH_SIZE', '250'))
SKIPPER_SELF_UPSTREAM = os.environ.get('SKIPPER_SELF_UPSTREAM', 'http://skipper.local:8000')


def split_list_str(input_str: str) -> List[str]:
    return [elem for elem in input_str.split(',') if elem != '']


SKIPPER_DJANGO_EXTRA_ALLOWED_HOSTS = split_list_str(os.environ.get('SKIPPER_DJANGO_EXTRA_ALLOWED_HOSTS', ''))
SKIPPER_DJANGO_EXTRA_LOGIN_REDIRECT_ALLOWED_HOSTS = split_list_str(os.environ.get('SKIPPER_DJANGO_EXTRA_LOGIN_REDIRECT_ALLOWED_HOSTS',
                                                                   ''))
SKIPPER_DJANGO_EXTRA_CORS_REGEX_WHITELIST = split_list_str(os.environ.get(
    'SKIPPER_DJANGO_EXTRA_CORS_REGEX_WHITELIST ', ''))
SKIPPER_DJANGO_EXTRA_CORS_WHITELIST = split_list_str(os.environ.get('SKIPPER_DJANGO_EXTRA_CORS_WHITELIST', ''))
SKIPPER_EXTRA_CSRF_TRUSTED_ORIGINS = split_list_str(os.environ.get('SKIPPER_EXTRA_CSRF_TRUSTED_ORIGINS', ''))
SKIPPER_DJANGO_DSP_FRAME_ANCESTORS = split_list_str(os.environ.get('SKIPPER_DJANGO_DSP_FRAME_ANCESTORS', ''))

if 'SKIPPER_SQL_LINT' in os.environ:
    SKIPPER_SQL_LINT = os.environ.get('SKIPPER_SQL_LINT', None)
else:
    SKIPPER_SQL_LINT = 'strict' if SKIPPER_TESTING or SKIPPER_DEBUG_RUN else None

if SKIPPER_SQL_LINT not in ['strict']:
    SKIPPER_SQL_LINT = None

# finally import all from environment_secret
from skipper.environment_secret import *