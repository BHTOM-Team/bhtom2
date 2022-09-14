![GitHub Workflow Status](https://img.shields.io/github/workflow/status/maja-jablonska/bhtom2/Django%20CI) ![GitHub issues](https://img.shields.io/github/issues/maja-jablonska/bhtom2) ![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/maja-jablonska/bhtom2) ![GitHub contributors](https://img.shields.io/github/contributors/maja-jablonska/bhtom2) ![GitHub last commit](https://img.shields.io/github/last-commit/maja-jablonska/bhtom2)

# BHTom 2

! **Important** Make sure to clone subrepositories as well:

```git submodule update --init --recursive```

# Local development (no docker)

**Prerequisite**: make sure to have the neweest PostgreSQL (14) installed

Development is done best on the local environment. This way you can generate new migrations in case of
database changes.

1. (Recommended) Create a conda environment
   1. ```conda create -n bhtom2```
   2. ```conda activate bhtom2```
2. Install the requirements:
   
   Use pip to install packages (only after using conda install, refer to https://www.anaconda.com/blog/using-pip-in-a-conda-environment for caveats)
   
   ```pip install -r requirements.txt```
   
   Why not conda? Unfortunately, some of the packages aren't in conda-forge :(
3. Create a local .env file

   ```cp template.env bhtom2/.bhtom.env```
   
   and fill the values in.
   Remember to input the values in ```"```.
   
   For local development, you will probably want to use localhost as the postgres and graylog host (although you can use a Dockerized/remote one if you wish!)
   
   ```
   POSTGRES_HOST="localhost"
   GRAYLOG_HOST="localhost"
   ```
4. Create a local DB (or an exposed Docker one, this is up to you)
   1. You can run the Docker/init.sql script on your local database. In case of any required changes, create a local copy of the script.
   2. Remember to fill the necessary values in the .bhtom.env file.
5. (ONLY AFTER CHANGES) Create the migrations. **Migrations are being commited to Github in order to ensure integration between all databases.** (Do watch out)
   1. ```python manage.py makemigrations```
   2. ```python manage.py makemigrations bhtom2```
6. After creating the migrations run the entrypoint.sh script.


# Building Docker

## Requirements

docker
docker-compose>1.25.0

1. Create a local .env file

   ```cp template.env bhtom2/.bhtom.env```
   
   and fill the values in.

## Command

In the Docker directory:

``COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --build``

## Environment

Environment settings are defined in Docker/.bhtom.env file.

This file is copied to bhtom2 directory in the Docker container and used the same way as on the local machine.
(It overwrites the local .bhtom.env, so no need to change that when changing something to the architecture.)

Refer to the template.env file for variable names.

# Testing

To run the tests provide your local database data in the ``.bhtom.env`` file.

Run the test using the following commands (in the main folder):

```bash
python manage.py test
```
This can take a while!

# Troubleshooting

- Make sure to clone subrepositories as well:

```git submodule update --init --recursive```

- Make sure that the ``bhtom`` user has the permission to create the test database. You might need to alter user in your local DB:

``ALTER USER bhtom CREATEDB;``

- Django>4.0 does not support Postgres<10 anymore. Make sure that you have the newest version.

- Make sure to allow for dev_entrypoint.sh execution.

``chmod +x dev_entrypoint.sh`` in UNIX-based systems (Linux, Mac OS)
