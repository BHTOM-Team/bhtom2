#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."
    while ! nc -z $SQL_HOST $SQL_PORT;do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

echo "Collecting static..."

while ! python3 manage.py collectstatic --no-input 2>&1;do
  echo "Collecting static..."
  sleep 3
done

echo "Migrating..."

while ! python3 manage.py migrate 2>&1;do
   echo "Migration is in progress..."
   sleep 3
done

echo "Add admin if not yet created..."
python3 manage.py add_admin

echo "Add catalogs if not yet created..."
python3 manage.py add_catalogs

echo "Django docker is fully configured."
echo "Running server..."

gunicorn --bind 0.0.0.0:8000 bhtom2.wsgi:application --log-level error --timeout 600 --workers 10 --threads 1 --access-logfile /data/log/gunicorn/bhtom-access.log --error-logfile /data/log/gunicorn/bhtom-error.log -k gevent
exec "$@"