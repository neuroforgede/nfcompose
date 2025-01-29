"""
This file contains all secrets.
By default it gets all credentials from the environment,
but to support customization like reading credentials
from a credential store at startup all these variables
are configured in a central place.

To override the behaviour of how the env vars are fetched,
simply overwrite this file at deploy-time with
something like a docker swarm secret
"""
import os

MANDATORY_ENV_VARS = {
    "SKIPPER_DJANGO_SECRET_KEY",
    "SKIPPER_DB",
    "SKIPPER_DB_USER",
    "SKIPPER_DB_PASSWD",
    "SKIPPER_DB_HOSTS",
    "SKIPPER_DB_PORTS",
    "SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET",
    "SKIPPER_S3_STATIC_BUCKET_NAME",
    "SKIPPER_S3_MEDIA_BUCKET_NAME",
}

env_var_keys = os.environ.keys()
not_set_vars = MANDATORY_ENV_VARS.difference(env_var_keys)
if len(not_set_vars) > 0:
    raise AssertionError(f'environment variables {str(not_set_vars)} are not set. exiting...')

SKIPPER_DJANGO_SECRET_KEY = os.environ['SKIPPER_DJANGO_SECRET_KEY']


SKIPPER_DB = os.environ['SKIPPER_DB']
SKIPPER_DB_USER = os.environ['SKIPPER_DB_USER']
SKIPPER_DB_PASSWD = os.environ['SKIPPER_DB_PASSWD']
SKIPPER_DB_HOSTS = os.environ['SKIPPER_DB_HOSTS']
SKIPPER_DB_PORTS = os.environ['SKIPPER_DB_PORTS']
SKIPPER_DB_SCHEMA = os.environ.get('SKIPPER_DB_SCHEMA', 'nf_compose')
SKIPPER_DB_SSL_ENABLE = os.environ.get('SKIPPER_DB_SSL_ENABLE', 'false') == 'true'
SKIPPER_DB_SSL_CERT = os.environ.get('SKIPPER_DB_SSL_CERT', '/certs/server.crt')
SKIPPER_DB_SSL_KEY = os.environ.get('SKIPPER_DB_SSL_KEY', '/certs/server.key')
SKIPPER_DB_SSL_ROOT_CERT = os.environ.get('SKIPPER_DB_SSL_ROOT_CERT', '/certs/rootCA.crt')
SKIPPER_DB_SSL_MODE = os.environ.get('SKIPPER_DB_SSL_MODE', 'verify-full')
SKIPPER_DB_TCP_CONNECT_TIMEOUT = os.environ.get('SKIPPER_DB_TCP_CONNECT_TIMEOUT', '10')
SKIPPER_DB_TCP_KEEPALIVES = os.environ.get('SKIPPER_DB_TCP_KEEPALIVES', '1')
SKIPPER_DB_TCP_KEEPALIVE_IDLE = os.environ.get('SKIPPER_DB_TCP_KEEPALIVE_IDLE', '60')
SKIPPER_DB_TCP_KEEPALIVE_INTERVAL = os.environ.get('SKIPPER_DB_TCP_KEEPALIVE_INTERVAL', '15')
SKIPPER_DB_POOL_HEALTHCHECK_TIMEOUT = float(os.environ.get('SKIPPER_DB_POOL_HEALTHCHECK_TIMEOUT', '5'))

SKIPPER_S3_DISABLE_INTERNAL_TO_EXTERNAL_TRANSLATION = os.environ.get('SKIPPER_S3_DISABLE_INTERNAL_TO_EXTERNAL_TRANSLATION', 'false') == 'true'

DEFAULT_S3_ACCESS_KEY_ID = os.environ.get('SKIPPER_S3_ACCESS_KEY_ID')
DEFAULT_S3_SECRET_ACCESS_KEY = os.environ.get('SKIPPER_S3_SECRET_ACCESS_KEY')
DEFAULT_S3_ENDPOINT_URL = os.environ.get('SKIPPER_S3_ENDPOINT_URL')
DEFAULT_S3_EXTERNAL_ENDPOINT_URL = os.environ.get('SKIPPER_S3_EXTERNAL_ENDPOINT_URL')
DEFAULT_S3_REGION_NAME = os.environ.get('SKIPPER_S3_REGION_NAME', 'eu-west-1')
# defaulting to path style to work with minio by default
DEFAULT_S3_ADDRESSING_STYLE = os.environ.get('SKIPPER_S3_ADDRESSING_STYLE', 'path')

SKIPPER_S3_MEDIA_ACCESS_KEY_ID = os.environ.get('SKIPPER_S3_MEDIA_ACCESS_KEY_ID', DEFAULT_S3_ACCESS_KEY_ID)
SKIPPER_S3_MEDIA_SECRET_ACCESS_KEY = os.environ.get('SKIPPER_S3_MEDIA_SECRET_ACCESS_KEY', DEFAULT_S3_SECRET_ACCESS_KEY)
SKIPPER_S3_MEDIA_ENDPOINT_URL = os.environ.get('SKIPPER_S3_MEDIA_ENDPOINT_URL', DEFAULT_S3_ENDPOINT_URL)
SKIPPER_S3_MEDIA_EXTERNAL_ENDPOINT_URL = os.environ.get('SKIPPER_S3_MEDIA_EXTERNAL_ENDPOINT_URL', DEFAULT_S3_EXTERNAL_ENDPOINT_URL)
SKIPPER_S3_MEDIA_BUCKET_NAME = os.environ['SKIPPER_S3_MEDIA_BUCKET_NAME']
SKIPPER_S3_MEDIA_REGION_NAME = os.environ.get('SKIPPER_S3_MEDIA_REGION_NAME', DEFAULT_S3_REGION_NAME)
SKIPPER_S3_MEDIA_ADDRESSING_STYLE = os.environ.get('SKIPPER_S3_MEDIA_ADDRESSING_STYLE', DEFAULT_S3_ADDRESSING_STYLE)
SKIPPER_S3_MEDIA_BASE_PATH = os.environ.get('SKIPPER_S3_MEDIA_BASE_PATH', '')

SKIPPER_S3_STATIC_ACCESS_KEY_ID = os.environ.get('SKIPPER_S3_STATIC_ACCESS_KEY_ID', DEFAULT_S3_ACCESS_KEY_ID)
SKIPPER_S3_STATIC_SECRET_ACCESS_KEY = os.environ.get('SKIPPER_S3_STATIC_SECRET_ACCESS_KEY', DEFAULT_S3_SECRET_ACCESS_KEY)
SKIPPER_S3_STATIC_ENDPOINT_URL = os.environ.get('SKIPPER_S3_STATIC_ENDPOINT_URL', DEFAULT_S3_ENDPOINT_URL)
SKIPPER_S3_STATIC_EXTERNAL_ENDPOINT_URL = os.environ.get('SKIPPER_S3_STATIC_EXTERNAL_ENDPOINT_URL', DEFAULT_S3_EXTERNAL_ENDPOINT_URL)
SKIPPER_S3_STATIC_BUCKET_NAME = os.environ['SKIPPER_S3_STATIC_BUCKET_NAME']
SKIPPER_S3_STATIC_REGION_NAME = os.environ.get('SKIPPER_S3_STATIC_REGION_NAME', DEFAULT_S3_REGION_NAME)
SKIPPER_S3_STATIC_ADDRESSING_STYLE = os.environ.get('SKIPPER_S3_STATIC_ADDRESSING_STYLE', DEFAULT_S3_ADDRESSING_STYLE)
SKIPPER_S3_STATIC_BASE_PATH = os.environ.get('SKIPPER_S3_STATIC_BASE_PATH', '')

def check_s3_settings() -> None:
    # Collect all variables we assigned earlier for MEDIA and STATIC, don't check *_EXTERNAL_ENDPOINT_URL as that is allowed to be empty
    variables_to_check = {
        'SKIPPER_S3_MEDIA_ACCESS_KEY_ID': SKIPPER_S3_MEDIA_ACCESS_KEY_ID,
        'SKIPPER_S3_MEDIA_SECRET_ACCESS_KEY': SKIPPER_S3_MEDIA_SECRET_ACCESS_KEY,
        'SKIPPER_S3_MEDIA_ENDPOINT_URL': SKIPPER_S3_MEDIA_ENDPOINT_URL,
        'SKIPPER_S3_MEDIA_BUCKET_NAME': SKIPPER_S3_MEDIA_BUCKET_NAME,
        'SKIPPER_S3_MEDIA_REGION_NAME': SKIPPER_S3_MEDIA_REGION_NAME,
        'SKIPPER_S3_STATIC_ACCESS_KEY_ID': SKIPPER_S3_STATIC_ACCESS_KEY_ID,
        'SKIPPER_S3_STATIC_SECRET_ACCESS_KEY': SKIPPER_S3_STATIC_SECRET_ACCESS_KEY,
        'SKIPPER_S3_STATIC_ENDPOINT_URL': SKIPPER_S3_STATIC_ENDPOINT_URL,
        'SKIPPER_S3_STATIC_BUCKET_NAME': SKIPPER_S3_STATIC_BUCKET_NAME,
        'SKIPPER_S3_STATIC_REGION_NAME': SKIPPER_S3_STATIC_REGION_NAME,
    }
    
    # Find any variables that are not set or are empty
    not_set_vars = [key for key, value in variables_to_check.items() if not value]
    
    # Raise an assertion error if any required variables are not set
    if not_set_vars:
        raise AssertionError(f"Environment variables {str(not_set_vars)} are not set. Either set the default values or provide all variables for static and media specific s3 settings.")

check_s3_settings()

SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET = os.environ["SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET"]

SKIPPER_REDIS_URL = os.environ.get('SKIPPER_REDIS_URL', 'redis://redis.local:6379')
SKIPPER_CELERY_BROKER_URL = os.environ.get('SKIPPER_CELERY_BROKER_URL', 'redis://redis.local:6379')
