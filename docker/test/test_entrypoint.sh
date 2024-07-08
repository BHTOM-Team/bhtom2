#!/bin/sh

echo "Copy config .env file to settings destination..."
mkdir /bhtom/settings/env
cp /env/.env /bhtom/settings/env/.bhtom.env

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

# Wait for few minute and run makemigrations
#while ! python manage.py makemigrations  2>&1; do
#   echo "Make migrations..."
#   sleep 3
#done

# Wait for few minute and run db migraiton
while ! python manage.py migrate  2>&1; do
   echo "Migration is in progress..."
   sleep 3
done

echo "Add admin if not yet created..."
python3 manage.py add_admin

echo "Add catalogs if not yet created..."
python3 manage.py add_catalogs

echo "Local django is fully configured."
echo "Running server..."

python3 manage.py runserver 0.0.0.0:8000
exec "$@"
