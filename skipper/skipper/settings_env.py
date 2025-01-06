# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

"""
Django settings for skipper project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Union
from skipper import environment

# rest of config

ROOT_API_PATH = "api/"
LOGIN_URL = 'api/common/auth/login'
LOGOUT_URL = 'api/common/auth/logout'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environment.SKIPPER_DJANGO_SECRET_KEY

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# COOKIE settings

SESSION_COOKIE_NAME = 'skipper-session'
SESSION_COOKIE_SECURE = not environment.SKIPPER_SESSION_INSECURE

# to login, we have to be on the same site,
# there we login with our session
# in order to use session cookie in cors requests
# we have to set samesite to none
# the rest of the security checks are done in the CORS
# settings
SESSION_COOKIE_SAMESITE = 'Lax'  #'Strict'
CSRF_USE_SESSIONS = True

# end COOKIE settings

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = environment.SKIPPER_DJANGO_DEBUG

SQL_LINT = environment.SKIPPER_SQL_LINT

if os.environ.get("RUN_MAIN") != "true":
    PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8001, 8050)

PROMETHEUS_EXPORT_MIGRATIONS = True
PROMETHEUS_METRIC_NAMESPACE = environment.SKIPPER_INSTALLATION_NAME

LOGIN_REDIRECT_URL = ('..')

URL_FIELD_NAME='url'

DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=1000

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'skipper.pagination.StandardResultsSetPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (        
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'skipper.core.authentication.PossiblyJWTTokenAuthentication',
        'skipper.core.authentication.PreSharedTokenAuthentication'
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    )
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        # ignore multitenant warnings about no tenant being set in admin
        'django_multitenant': {
            'level': 'ERROR'
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        }
    },
}

SKIPPER_MODULES_SETTINGS = {
    'skipper.dataseries': {
        'base_path': ROOT_API_PATH,
        'sub_modules': ['skipper.dataseries.storage.dynamic_sql'],
        'include_nodered_etl': True
    },
    'skipper.common': {
        'base_path': ROOT_API_PATH
    },
    'skipper.app': {
        # the app module is named app so we only need the empty base_url here
        'base_path': ''
    },
    'skipper.flow': {
        'base_path': ROOT_API_PATH
    },
    'skipper.health': {
        'base_path': ROOT_API_PATH
    },
    'skipper.task': {
        'base_path': ROOT_API_PATH
    },
    'skipper.debug': {
        'base_path': ROOT_API_PATH
    },
    'skipper.core': {
        'base_path': ROOT_API_PATH
    }
}

# the upstream that nginx sees
SKIPPER_DEFAULT_SYSTEM_SECRET = environment.SKIPPER_FLOW_DEFAULT_SYSTEM_SECRET

SKIPPER_DEFAULT_NODE_RED_UPSTREAM = environment.SKIPPER_FLOW_DEFAULT_NODE_RED_UPSTREAM
SKIPPER_DEFAULT_TASK_DASHBOARD_UPSTREAM = environment.SKIPPER_TASK_DASHBOARD_UPSTREAM

SKIPPER_DEFAULT_NODE_RED_INTERNAL_UPSTREAM = environment.SKIPPER_FLOW_DEFAULT_NODE_RED_INTERNAL_UPSTREAM
if environment.SKIPPER_FLOW_DEFAULT_NODE_RED_ENABLED:
    SKIPPER_NODE_RED_UPSTREAMS = {
        "default":  {
            "url": SKIPPER_DEFAULT_NODE_RED_UPSTREAM,
            "internal_url": SKIPPER_DEFAULT_NODE_RED_INTERNAL_UPSTREAM
        }
    }
else:
    SKIPPER_NODE_RED_UPSTREAMS = {}

if TYPE_CHECKING:
    from skipper.core.models.tenant import Tenant
    from django.contrib.auth.models import User, AnonymousUser
    from django.http import HttpRequest
else:
    Tenant = object
    User = object
    HttpRequest = object
    AnonymousUser = object


def flow_system_secret(tenant: Tenant, user: Optional[Union[User, AnonymousUser]], request: Optional[HttpRequest]) -> str:
    return SKIPPER_DEFAULT_SYSTEM_SECRET


def flow_upstream_edit(tenant: Tenant, user: User, request: HttpRequest) -> str:
    return SKIPPER_DEFAULT_NODE_RED_UPSTREAM


def flow_upstream_impl(tenant: Tenant, user: Optional[Union[User, AnonymousUser]], request: HttpRequest) -> str:
    return SKIPPER_DEFAULT_NODE_RED_UPSTREAM


def task_upstream_dashboard(tenant: Tenant, user: Optional[Union[User, AnonymousUser]], request: HttpRequest) -> str:
    return SKIPPER_DEFAULT_TASK_DASHBOARD_UPSTREAM


MAINTENANCE_MODE = False
MAINTENANCE_USER_ID = None

SKIPPER_MODULES = [k for k, v in SKIPPER_MODULES_SETTINGS.items()]
SKIPPER_SUB_MODULES = [
    item
    for k, module_settings in SKIPPER_MODULES_SETTINGS.items()  # type: ignore
    for item in (module_settings['sub_modules'] if 'sub_modules' in module_settings else [])  # type: ignore
]

SKIPPER_DATA_SERIES_BULK_TASK_SIZE = environment.SKIPPER_DATA_SERIES_BULK_TASK_SIZE
SKIPPER_DATA_SERIES_BULK_BATCH_SIZE = environment.SKIPPER_DATA_SERIES_BULK_BATCH_SIZE

SKIPPER_CONTAINER_UPSTREAM = environment.SKIPPER_SELF_UPSTREAM

SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION':  True,
    # the old stuff should still
    'AUTH_HEADER_TYPES': ('Bearer', 'Token' )
}

SITE_ID = 1
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_extensions',
    'django_filters',
    'storages',
    'guardian',
    'django_multitenant',
    'pgq',
    'corsheaders',
    'rest_framework.authtoken',
    'django_prometheus',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    'health_check',  # required
    'health_check.db',  # stock Django health checkers
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.celery',  # requires celery
    'health_check.contrib.s3boto3_storage',  # requires boto and S3BotoStorage backend
    'health_check.contrib.redis',  # required Redis broker
    'django_celery_results',
] + SKIPPER_MODULES + SKIPPER_SUB_MODULES + [
    'skipper.main',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'skipper.core.middleware.TrackCurrentRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    "django_permissions_policy.PermissionsPolicyMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'skipper.core.middleware.TenantFromUserMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'
CSP_FRAME_ANCESTORS = [
    "'self'",
    *environment.SKIPPER_DJANGO_DSP_FRAME_ANCESTORS
]

csp_static_url = f'{environment.SKIPPER_S3_ENDPOINT_URL}/{environment.SKIPPER_S3_STATIC_BUCKET_NAME}/'

CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", csp_static_url)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", csp_static_url)
CSP_FONT_SRC = ("'self'", csp_static_url)
CSP_IMG_SRC = ("'self'", csp_static_url)

PERMISSIONS_POLICY: Dict[str, Any] = {
    # just something we definitely dont do so that we get a better rating
    'payment': [],
}

ROOT_URLCONF = 'skipper.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, os.path.join(BASE_DIR, 'skipper', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'skipper.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

SYSTEM_POSTGRES_DATABASE_ROLES: List[str] = [environment.SKIPPER_DB_USER]

skipper_container_type = environment.SKIPPER_CONTAINER_TYPE
_db_ssl_settings = (
    {
        'sslcert': environment.SKIPPER_DB_SSL_CERT,
        'sslkey': environment.SKIPPER_DB_SSL_KEY,
        'sslrootcert': environment.SKIPPER_DB_SSL_ROOT_CERT,
        'sslmode': environment.SKIPPER_DB_SSL_MODE,
    } if environment.SKIPPER_DB_SSL_ENABLE else {}
)
_db_engine = 'django.db.backends.postgresql'

_db_options = {}
if skipper_container_type in ['DJANGO', 'DJANGO_INTERNAL'] and not environment.SKIPPER_TESTING and not TYPE_CHECKING and not (os.environ.get('MYPY_RUN', 'false') == 'true'):
    _db_options = {
        'pool': {
            'min_size': max(2, environment.SKIPPER_GUNICORN_WORKER_CONCURRENCY),
            'max_size': max(2, environment.SKIPPER_GUNICORN_WORKER_CONCURRENCY),
            'timeout': environment.SKIPPER_GUNICORN_WORKER_DB_POOL_TIMEOUT
        }
    }
else:
    _db_options = {
        'pool': {
            'min_size': max(2, environment.SKIPPER_CELERY_WORKER_CONCURRENCY),
            'max_size': max(2, environment.SKIPPER_CELERY_WORKER_CONCURRENCY),
            'timeout': environment.SKIPPER_CELERY_WORKER_DB_POOL_TIMEOUT
        }
    }

if environment.SKIPPER_TESTING or TYPE_CHECKING:
    _db_options = {}

if os.environ.get('MYPY_RUN', 'false') == 'true':
    DATABASES: Dict[str, Any] = {}
else:
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'NAME': environment.SKIPPER_DB,
            'USER': environment.SKIPPER_DB_USER,
            'PASSWORD': environment.SKIPPER_DB_PASSWD,
            'HOST': environment.SKIPPER_DB_HOSTS,
            'CONN_MAX_AGE': 0,
            'CONN_HEALTH_CHECKS': True,
            'PORT': environment.SKIPPER_DB_PORTS,
            'OPTIONS': {
                'application_name': f'skipper_{environment.SKIPPER_INSTALLATION_NAME}_{skipper_container_type}',
                'options': f'-c search_path={environment.SKIPPER_DB_SCHEMA}',
                'target_session_attrs': 'read-write',
                'connect_timeout': environment.SKIPPER_DB_TCP_CONNECT_TIMEOUT,
                'keepalives': environment.SKIPPER_DB_TCP_KEEPALIVES,
                'keepalives_idle': environment.SKIPPER_DB_TCP_KEEPALIVE_IDLE,
                'keepalives_interval': environment.SKIPPER_DB_TCP_KEEPALIVE_INTERVAL,
                **_db_options, # type: ignore
                **_db_ssl_settings,
            },
            'ATOMIC_REQUESTS': True
        }
    }

DATA_SERIES_DYNAMIC_SQL_DB_READ = 'default'
DATA_SERIES_DYNAMIC_SQL_DB = 'default'
DATA_SERIES_DYNAMIC_SQL_DB_BULK = 'default'
CELERY_DATABASES = DATABASES
DATABASE_ROUTERS = ['skipper.core.db_routers.DynamicSQLRouter']

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

if environment.SKIPPER_TESTING:
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher'
    ]
else:
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
        'django.contrib.auth.hashers.Argon2PasswordHasher',
        'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    ]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

SKIPPER_USE_S3 = True
AWS_DEFAULT_ACL = None
AWS_BUCKET_ACL = None


# use externally managed S3
AWS_ACCESS_KEY_ID = environment.SKIPPER_S3_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = environment.SKIPPER_S3_SECRET_ACCESS_KEY
# TODO: remove this, its deprecated
AWS_S3_OUTSIDE_URL = environment.SKIPPER_S3_ENDPOINT_URL

# just always replace the domain with the outside domain
AWS_S3_URL_TRANSLATE_TO_OUTSIDE_URL = [
    {
        'match': {
            'any': True,
            # 'scheme': 'http',
            # 'host': '...'
        },
        'replace': {
            'scheme': environment.SKIPPER_S3_ENDPOINT_SCHEME,
            'host': environment.SKIPPER_S3_ENDPOINT_NETLOC
        }
    }
]
AWS_S3_ENDPOINT_URL = environment.SKIPPER_S3_INTERNAL_ENDPOINT_URL
AWS_S3_REGION_NAME = 'eu-west-1'

STORAGES = {
    'staticfiles': {
        'BACKEND': 'skipper.core.storage.static.S3Boto3StaticStorage'
    },
    'default': {
        'BACKEND': 'skipper.core.storage.media.S3Boto3MediaStorage'
    }
}
# by default use the authenticated one
AWS_STORAGE_BUCKET_NAME = environment.SKIPPER_S3_MEDIA_BUCKET_NAME
NF_AWS_STORAGE_BUCKET_NAME_STATIC = environment.SKIPPER_S3_STATIC_BUCKET_NAME
NF_AWS_QUERYSTRING_AUTH_STATIC = False

NF_AWS_STORAGE_BUCKET_NAME_MEDIA = environment.SKIPPER_S3_MEDIA_BUCKET_NAME



AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_LOCATION = ''
AWS_AUTO_CREATE_BUCKET = True
S3_USE_SIGV4 = True


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'skipper', 'static')
]


STATIC_URL = '/' + ROOT_API_PATH + 'static/'

# used for url in common module, therefore we need it separated
# out from the media_url itself which is required for imagefield
# to work
COMMON_MODULE_URL_REPRESENTATION = 'common'
MEDIA_URL_LAST_PART = '/media/'
MEDIA_URL = '/' + ROOT_API_PATH + COMMON_MODULE_URL_REPRESENTATION + '/' + MEDIA_URL_LAST_PART

STATIC_ROOT = "static/"
# TODO: probably unused, delete?
MEDIA_ROOT = "media/"

APP_ROOT = "app-content/"
FILE_UPLOAD_PERMISSIONS = 0o644

# max body size is a bit larger than for normal apps
DATA_UPLOAD_MAX_MEMORY_SIZE = 262144000 # 250MB
# Anything above 2.5 MB should be streamed to a tmp file
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440 # 2.5MB

# CSRF RELEVANT SETTINGS
BASE_DOMAIN = environment.SKIPPER_DOMAIN

# CSRF RELEVANT SETTINGS
ALLOWED_HOSTS = [
    BASE_DOMAIN,
    f'.{BASE_DOMAIN}',
    'skipper.local',
    'skipper.internal.local',
    *environment.SKIPPER_DJANGO_EXTRA_ALLOWED_HOSTS
]  # type: ignore



# -> TODO: change these so that they are tenant specific
LOGIN_REDIRECT_ALLOWED_HOSTS = environment.SKIPPER_DJANGO_EXTRA_LOGIN_REDIRECT_ALLOWED_HOSTS
CORS_ORIGIN_WHITELIST = environment.SKIPPER_DJANGO_EXTRA_CORS_WHITELIST
CORS_ORIGIN_REGEX_WHITELIST = environment.SKIPPER_DJANGO_EXTRA_CORS_REGEX_WHITELIST
CORS_ALLOW_CREDENTIALS = True

# THIS DOES NOT SEEM TO WORK:
# ## required so that the csrf checks work (they set a valid trusted origin so that the csrf middleware works)
# ## CORS_REPLACE_HTTPS_REFERER = True
# therefore: we have to manually specify the trusted origins
# (TODO: do this tenant specific => custom csrf middleware required?)
CSRF_TRUSTED_ORIGINS = environment.SKIPPER_EXTRA_CSRF_TRUSTED_ORIGINS

REDIS_URL = environment.SKIPPER_REDIS_URL

# CELERY STUFF
CELERY_BROKER_URL = environment.SKIPPER_CELERY_BROKER_URL

SKIPPER_CELERY_EVENT_QUEUE_HEARTBEAT_SCHEDULE = environment.SKIPPER_CELERY_EVENT_QUEUE_HEARTBEAT_SCHEDULE
SKIPPER_CELERY_EVENT_QUEUE_CLEANUP_SCHEDULE = environment.SKIPPER_CELERY_EVENT_QUEUE_CLEANUP_SCHEDULE
SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_SCHEDULE = environment.SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_SCHEDULE
SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_MAX_AGE_HOURS = environment.SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_MAX_AGE_HOURS
SKIPPER_CELERY_DATA_SERIES_HISTORY_CLEANUP_SCHEDULE = environment.SKIPPER_CELERY_DATA_SERIES_HISTORY_CLEANUP_SCHEDULE
SKIPPER_CELERY_DATA_SERIES_META_MODEL_CLEANUP_SCHEDULE = environment.SKIPPER_CELERY_DATA_SERIES_META_MODEL_CLEANUP_SCHEDULE
SKIPPER_CELERY_PERSIST_DATA_POINT_CHUNK_REQUEUE_SCHEDULE = environment.SKIPPER_CELERY_PERSIST_DATA_POINT_CHUNK_REQUEUE_SCHEDULE
SKIPPER_CELERY_HEALTH_CHECK_HEARTBEAT_SCHEDULE = environment.SKIPPER_CELERY_HEALTH_CHECK_HEARTBEAT_SCHEDULE
SKIPPER_CELERY_OUTSTANDING_TOKENS_CLEANUP_SCHEDULE = environment.SKIPPER_CELERY_OUTSTANDING_TOKENS_CLEANUP_SCHEDULE

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# keep task results for 30 days. since we ignore all results
# this is essentially an error queue
# (documentation in celery states CELERY_TASK_RESULT_EXPIRES, but code shows CELERY_RESULT_EXPIRES is correct)
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24 * 30
CELERY_RESULT_EXPIRES = 60 * 60 * 24 * 30
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True
