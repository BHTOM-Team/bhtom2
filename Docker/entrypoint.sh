#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

#echo "Flushing manage.py..."
#
#while ! python manage.py flush --no-input 2>&1; do
#  echo "Flushing manage.py..."
#  sleep 3
#done

echo "Collecting static..."

while ! python3 manage.py collectstatic --no-input 2>&1; do
  echo "Collecting static..."
  sleep 3
done

#echo "Making migrations..."
#
#while ! python manage.py makemigrations 2>&1; do
#  echo "making migrations..."
#  sleep 3
#done

echo "Migrating..."

# Wait for few minute and run db migration
while ! python3 manage.py migrate  2>&1; do
   echo "Migration is in progress..."
   sleep 3
done

echo "Add admin if not yet created..."
python3 manage.py add_admin

echo "Django docker is fully configured."

echo "Running server..."

python3 manage.py runserver 0.0.0.0:8000

exec "$@"