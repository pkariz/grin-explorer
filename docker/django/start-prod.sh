#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
set -o xtrace

pipenv run python manage.py migrate
# for django-admin page
pipenv run python manage.py collectstatic --noinput
pipenv run gunicorn backend.wsgi:application --bind 0.0.0.0:8000
