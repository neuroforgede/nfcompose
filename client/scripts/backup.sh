#!/bin/bash

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

KILLED="no"
trap ctrl_c INT
function ctrl_c() {
    KILLED="yes"
}

now=$(TZ=UTC date '+%Y-%m-%dT%H:%M:%S.%3N')

source venv/bin/activate
source ./.env

BASE_BACKUP_FOLDER=backup
mkdir -p $BASE_BACKUP_FOLDER
check_result "failed to create backup folder at $BASE_BACKUP_FOLDER"

last_sync=$(cat $BASE_BACKUP_FOLDER/last_sync.txt 2> /dev/null || bash -c "echo -n ''")
check_result "failed to get last sync date"

changes_since_str=""
if [ "$last_sync" == "" ]; then
  echo "no last_sync date found. full run."
  changes_since_str=""
else
  echo "last sync ran at $last_sync. using --changes-since=$last_sync"
  changes_since_str="--changes-since=$last_sync"
fi

compose_cli dump dataseries ${NF_COMPOSE_URL} --compose-user ${NF_COMPOSE_USER} --compose-password ${NF_COMPOSE_PASSWORD} | jfq --jsonlines-output "$.data_series.external_id" | while read external_id; do
    if [ "$KILLED" == "no" ]; then
        echo "backing up $external_id ..."

        DATA_SERIES_DIR=$BASE_BACKUP_FOLDER/$external_id/$now
        mkdir -p "$DATA_SERIES_DIR"
        check_result "failed to create $DATA_SERIES_DIR"

        EXTRA_FILE_DIR=$DATA_SERIES_DIR/files
        mkdir -p $EXTRA_FILE_DIR
        check_result "failed to extra file dir for $external_id at $EXTRA_FILE_DIR"

        JSONL_FILE=$DATA_SERIES_DIR/datapoints.jsonl

        compose_cli dump datapoints ${NF_COMPOSE_URL} \
            --compose-user ${NF_COMPOSE_USER} \
            --compose-password ${NF_COMPOSE_PASSWORD} \
            --outfile $JSONL_FILE \
            --lines \
            --pagesize 10 \
            --extra-file-dir $EXTRA_FILE_DIR \
            $changes_since_str \
            $external_id
        check_result "failed to run backup for dataseries $external_id"
    fi
done
check_result "failed backups..."

if [ "$KILLED" == "no" ]; then
    one_hour_ago=$(TZ=UTC date -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S.%3N')
    check_result "failed to get one_hour_ago"
    echo -n "$one_hour_ago" > $BASE_BACKUP_FOLDER/last_sync.txt
    check_result "failed to write last_sync.txt"
fi

if [ -n "$FINISHED_PING_URL" ]; then
    curl "$FINISHED_PING_URL"
    check_result "failed to ping $FINISHED_PING_URL"
else
    echo "no FINISHED_PING_URL specified"
fi

echo "success."