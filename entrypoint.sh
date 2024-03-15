#!/bin/sh

echo "Collecting static files..."
python manage.py collectstatic --no-input

# Check if the db.sqlite3 file exists
if [ ! -f "db.sqlite3" ]; then
    echo "Migrating database..."
    python manage.py migrate
else

exec "$@"
