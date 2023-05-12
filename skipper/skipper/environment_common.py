"""
This file contains all env vars that we need from inside the code.
Since we dont have all deployments moved to env variable deployments
we have these here so that deployments that mount the settings.py
don't crashloop because of missing env vars.
"""
import os


SKIPPER_OTEL_TELEMETRY_ENABLED = os.environ.get('SKIPPER_OTEL_TELEMETRY_ENABLED', 'false') == 'true'
SKIPPER_OTEL_SERVICE_NAME = os.environ.get('SKIPPER_OTEL_SERVICE_NAME', None)
SKIPPER_OTEL_JAEGER_AGENT_HOST_NAME = os.environ.get('SKIPPER_OTEL_JAEGER_AGENT_HOST_NAME', 'jaeger.local')
SKIPPER_OTEL_JAEGER_AGENT_PORT = int(os.environ.get('SKIPPER_OTEL_JAEGER_AGENT_PORT', 6831))
SKIPPER_OTEL_JAEGER_COLLECTOR_ENDPOINT = os.environ.get('SKIPPER_OTEL_JAEGER_COLLECTOR_ENDPOINT', None)
SKIPPER_OTEL_JAEGER_USERNAME = os.environ.get('SKIPPER_OTEL_JAEGER_USERNAME', None)
SKIPPER_OTEL_JAEGER_PASSWORD = os.environ.get('SKIPPER_OTEL_JAEGER_PASSWORD', None)
SKIPPER_OTEL_JAEGER_MAX_TAG_VALUE_LENGTH = os.environ.get('SKIPPER_OTEL_JAEGER_MAX_TAG_VALUE_LENGTH', None)

SKIPPER_OTEL_JAEGER_UI_ENABLED = os.environ.get('SKIPPER_OTEL_JAEGER_UI_ENABLED', 'false') == 'true'
SKIPPER_OTEL_JAEGER_UI_UPSTREAM = os.environ.get('SKIPPER_OTEL_JAEGER_UI_UPSTREAM', f'http://jaeger.local:16686')

SKIPPER_INSTALLATION_NAME = os.environ.get('SKIPPER_INSTALLATION_NAME', 'default')

SKIPPER_TASK_DASHBOARD_ENABLED = os.environ.get('SKIPPER_TASK_DASHBOARD_ENABLED', 'false') == 'true'
SKIPPER_TASK_DASHBOARD_UPSTREAM = os.environ.get('SKIPPER_TASK_DASHBOARD_UPSTREAM', "http://skipper.task.dashboard.local:5555")

# dataseries consumers

SKIPPER_CELERY_EVENT_QUEUE_MAX_EVENTS_PER_CONSUMER_HEARTBEAT = int(os.environ.get('SKIPPER_CELERY_EVENT_QUEUE_MAX_EVENTS_PER_CONSUMER_HEARTBEAT', 200))
SKIPPER_CONSUMER_PROXY_URL = os.environ.get('SKIPPER_CONSUMER_PROXY_URL', None)