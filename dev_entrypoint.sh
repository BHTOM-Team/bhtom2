#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Collecting static..."

while ! python manage.py collectstatic --no-input 2>&1; do
  echo "Collecting static..."
  sleep 3
done

echo "Migrating..."

# Wait for few minute and run db migraiton
while ! python manage.py migrate  2>&1; do
   echo "Migration is in progress..."
   sleep 3
done

echo "Local django is fully configured."

echo "Running server..."

python manage.py runserver localhost:8000

exec "$@"
