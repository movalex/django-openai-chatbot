#!/bin/sh
set -e

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Applying migrations..."
python manage.py migrate --no-input

exec "$@"
