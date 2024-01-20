#!/bin/bash

source venv/bin/activate
source ./.env

compose_cli dump dataseries ${NF_COMPOSE_URL} --compose-user ${NF_COMPOSE_USER} --compose-password ${NF_COMPOSE_PASSWORD} --domain-aliases "${NF_COMPOSE_DOMAIN_ALIASES}" --regex-filter "${NF_COMPOSE_DATASERIES_REGEX}" --outfile compose/dataseries.json