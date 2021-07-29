#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Flushing manage.py..."

while ! python manage.py flush --no-input 2>&1; do
  echo "Flushing manage.py..."
  sleep 3
done

echo "Collecting static..."

while ! python manage.py collectstatic --no-input 2>&1; do
  echo "Collecting static..."
  sleep 3
done

echo "Making migrations..."

while ! python manage.py makemigrations 2>&1; do
  echo "making migrations..."
  sleep 3
done

while ! python manage.py makemigrations bhtom2 2>&1; do
  echo "making migrations for bhtom2..."
  sleep 3
done

echo "Migrating..."

# Wait for few minute and run db migraiton
while ! python manage.py migrate  2>&1; do
   echo "Migration is in progress..."
   sleep 3
done

echo "Django docker is fully configured."

echo "Running server..."

python manage.py runserver 0.0.0.0:8000

exec "$@"
