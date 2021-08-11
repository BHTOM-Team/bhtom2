# Building

## Requirements

docker
docker-compose>1.25.0

## Command

In the Docker directory:

``COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --build``

# Testing

To run the tests provide your local database data in the ``.bhtom.env`` file.

## Troubleshooting

Make sure that the ``bhtom`` user has the permission to create the test database. You might need to alter user in your local DB:

``ALTER USER bhtom CREATEDB;``