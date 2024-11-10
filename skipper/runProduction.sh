#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


worker_count="${SKIPPER_WORKER_COUNT}"
worker_type="${SKIPPER_WORKER_TYPE}"
worker_timeout="${SKIPPER_WORKER_TIMEOUT}"
log_level="${SKIPPER_LOG_LEVEL}"
bind_ip="${SKIPPER_BIND_IP}"

celery_worker_concurrency="${SKIPPER_CELERY_WORKER_CONCURRENCY}"
celery_worker_queues="${SKIPPER_CELERY_WORKER_QUEUES}"

statsd_host="${SKIPPER_STATSD_HOST}"
statsd_prefix="${SKIPPER_STATSD_PREFIX}"

gunicorn_limit_request_line="${SKIPPER_GUNICORN_LIMIT_REQUEST_LINE}"
gunicorn_access_log_format="${SKIPPER_GUNICORN_ACCESS_LOG_FORMAT}"
gunicorn_worker_tmp_dir="${SKIPPER_GUNICORN_WORKER_TMP_DIR}"

skipper_singlebeat_enabled="${SKIPPER_SINGLE_BEAT_ENABLED}"


if [ -z "$statsd_prefix" ]; then
    statsd_prefix='skipper.app'
fi

statsd_gunicorn_params=""

if [ -z "$statsd_host" ]; then
    echo "running without statsd..."
else
    statsd_gunicorn_params="--statsd-host=${statsd_host} --statsd-prefix=${statsd_prefix}"
fi

if [ -z "$worker_count" ]; then
    worker_count="3"
fi

if [ -z "$worker_timeout" ]; then
    # keep the (rather aggressive) default from gunicorn
    worker_timeout="30"
fi

if [ -z "$gunicorn_limit_request_line" ]; then
    gunicorn_limit_request_line="4094"
fi

if [ -z "$worker_type" ]; then
    worker_type="gevent"
fi

if [ -z "$celery_worker_concurrency" ]; then
    celery_worker_concurrency="2"
fi

if [ -z "$celery_worker_queues" ]; then
    celery_worker_queues="celery,event_queue,event_cleanup,health_check,data_series_cleanup,persist_data,file_registry_cleanup,index_creation,requeue_persist_data"
fi

if [ -z "$log_level" ]; then
    log_level="warning"
fi

if [ -z "$bind_ip" ]; then
    bind_ip="0.0.0.0"
fi

if [ -z "$gunicorn_access_log_format" ]; then
    gunicorn_access_log_format='%(h)s %(l)s %({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
fi

if [ -z "$gunicorn_worker_tmp_dir" ]; then
    # default to /tmp as we dont want to break existing behaviour
    gunicorn_worker_tmp_dir="/tmp"
fi

if [ -z "$skipper_singlebeat_enabled" ]; then
    skipper_singlebeat_enabled="no"
fi

if [ "${skipper_singlebeat_enabled}" == "yes" ]; then
    single_beat_cmd_prefix="single-beat"
else
    single_beat_cmd_prefix=""
fi

if [ "${SKIPPER_CONTAINER_TYPE}" == "CELERY" ]; then
  cd /neuroforge/skipper || (echo "/neuroforge/skipper does not exist" && exit 1)
  exec celery \
    -A skipper \
    worker \
    -O fair \
    -Q $celery_worker_queues \
    --loglevel=INFO \
    --pool=gevent
    --concurrency=$celery_worker_concurrency
elif [ "${SKIPPER_CONTAINER_TYPE}" == "CELERY_BEAT" ]; then
  cd /neuroforge/skipper || (echo "/neuroforge/skipper does not exist" && exit 1)
  rm /neuroforge/skipper/celery.pid || (echo "did not find /neuroforge/skipper/celery.pid. continuing...")
  exec $single_beat_cmd_prefix celery \
    -A skipper \
    beat \
    --pidfile=/neuroforge/skipper/celery.pid \
    --loglevel=INFO
elif [ "${SKIPPER_CONTAINER_TYPE}" == "TASK_DASHBOARD" ]; then
  cd /neuroforge/skipper || (echo "/neuroforge/skipper does not exist" && exit 1)
  exec $single_beat_cmd_prefix celery \
  -A skipper \
  flower \
  --port=5555 \
  --url_prefix=/api/task/dashboard
else
  cd /neuroforge/skipper || (echo "/neuroforge/skipper does not exist" && exit 1)
  # we want splitting here
  # shellcheck disable=SC2086
  SKIPPER_GUNICORN=true exec gunicorn \
    --timeout "${worker_timeout}" \
    --capture-output \
    --access-logfile - \
    --error-logfile - \
    --log-file - \
    --log-level $log_level \
    --worker-tmp-dir $gunicorn_worker_tmp_dir \
    --access-logformat "$gunicorn_access_log_format" \
    -k $worker_type \
    --workers=$worker_count \
    ${statsd_gunicorn_params} \
    --limit-request-line "$gunicorn_limit_request_line" \
    -c python:skipper.gunicorn \
    -b $bind_ip:8000 \
    skipper.wsgi
fi


