check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

NF_COMPOSE_TENANT_NAME="default"
NF_COMPOSE_USER="admin"
NF_COMPOSE_PASSWORD="admin"

cd /neuroforge/skipper

python manage.py migrate --no-input
check_result "failed to run migrations"

python manage.py create_tenant --name "${NF_COMPOSE_TENANT_NAME}" --upsert
check_result "failed to create tenant ${NF_COMPOSE_TENANT_NAME}"

python manage.py create_user --tenant "${NF_COMPOSE_TENANT_NAME}" --username "${NF_COMPOSE_USER}" --password "${NF_COMPOSE_PASSWORD}" --staff --superuser --upsert
check_result "failed to create user ${NF_COMPOSE_USER}"

python manage.py collectstatic --noinput
check_result "failed to collect static files"