#!/bin/bash
python3 -m pipenv run python3 manage.py create_tenant --name nf --upsert
python3 -m pipenv run python3 manage.py create_user --tenant nf --username nf --password nf --staff --superuser --upsert

