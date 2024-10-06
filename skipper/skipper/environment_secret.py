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
    "SKIPPER_S3_ACCESS_KEY_ID",
    "SKIPPER_S3_SECRET_ACCESS_KEY",
    "SKIPPER_S3_ENDPOINT_URL",
    "SKIPPER_S3_INTERNAL_ENDPOINT_URL",
    "SKIPPER_S3_MEDIA_BUCKET_NAME",
    "SKIPPER_S3_STATIC_BUCKET_NAME",
    "SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET"
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

SKIPPER_S3_ACCESS_KEY_ID = os.environ['SKIPPER_S3_ACCESS_KEY_ID']
SKIPPER_S3_SECRET_ACCESS_KEY = os.environ['SKIPPER_S3_SECRET_ACCESS_KEY']
SKIPPER_S3_ENDPOINT_URL = os.environ['SKIPPER_S3_ENDPOINT_URL']
SKIPPER_S3_INTERNAL_ENDPOINT_URL = os.environ.get('SKIPPER_S3_INTERNAL_ENDPOINT_URL', SKIPPER_S3_ENDPOINT_URL)
SKIPPER_S3_MEDIA_BUCKET_NAME = os.environ['SKIPPER_S3_MEDIA_BUCKET_NAME']
SKIPPER_S3_STATIC_BUCKET_NAME = os.environ['SKIPPER_S3_STATIC_BUCKET_NAME']

SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET = os.environ["SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET"]

SKIPPER_REDIS_URL = os.environ.get('SKIPPER_REDIS_URL', 'redis://redis.local:6379')
SKIPPER_CELERY_BROKER_URL = os.environ.get('SKIPPER_CELERY_BROKER_URL', 'redis://redis.local:6379')