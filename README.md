# Local development

Development is done best on the local environment. This way you can generate new migrations in case of
database changes.

1. Create a local DB (or an exposed Docker one, this is up to you)
   1. You can run the Docker/init.sql script on your local database. In case of any required changes, create a local copy of the script.
   2. Remember to fill the necessary values in the .bhtom.env file.
2. Create the migrations. **Migrations are being commited to Github in order to ensure integration between all databases.** (Do watch out)
   1. ```python manage.py makemigrations```
   2. ```python manage.py makemigrations bhtom2```
3. After creating the migrations run the dev_entrypoint.sh script.


# Building Docker

## Requirements

docker
docker-compose>1.25.0

## Command

In the Docker directory:

``COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --build``

## Environment

Environment settings are defined in Docker/.bhtom.env file.

This file is copied to bhtom2 directory in the Docker container and used the same way as on the local machine.
(It overwrites the local .bhtom.env, so no need to change that when changing something to the architecture.)

# Testing

To run the tests provide your local database data in the ``.bhtom.env`` file.

# Troubleshooting

- Make sure that the ``bhtom`` user has the permission to create the test database. You might need to alter user in your local DB:

``ALTER USER bhtom CREATEDB;``

- Make sure to allow for dev_entrypoint.sh execution.

``chmod +x dev_entrypoint.sh`` in UNIX-based systems (Linux, Mac OS)