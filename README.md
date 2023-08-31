![GitHub Workflow Status](https://img.shields.io/github/workflow/status/maja-jablonska/bhtom2/Django%20CI) ![GitHub issues](https://img.shields.io/github/issues/maja-jablonska/bhtom2) ![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/maja-jablonska/bhtom2) ![GitHub contributors](https://img.shields.io/github/contributors/maja-jablonska/bhtom2) ![GitHub last commit](https://img.shields.io/github/last-commit/maja-jablonska/bhtom2)

# BHTom 2

! **Important** Make sure to clone subrepositories as well:

```git submodule foreach --recursive git reset --hard```

and then update all subrepositories:

```git submodule update --init --recursive --remote```

! **Important** Make sure to have at least Python 3.8 or newer

# Local development (no docker)

**Prerequisite**: make sure to have the neweest PostgreSQL (14) installed

Development is done best on the local environment. This way you can generate new migrations in case of
database changes.

1. (Recommended) Create a conda environment
   1. ```conda create -n bhtom2 python=3.9```
   2. ```conda activate bhtom2```
   3. ```conda install pip``` - so that the local env pip is used, not the global one.
2. Install the requirements:
   
   Use pip to install packages (only after using conda install, refer to https://www.anaconda.com/blog/using-pip-in-a-conda-environment for caveats)
   
   ```pip install -r requirements.txt```
   
   Why not conda? Unfortunately, some of the packages aren't in conda-forge :(
3. Create a local .env file

   ```cp template.env bhtom2/.bhtom.env```
   
   and fill the values in.
   Remember to input the values in ```"```.
   
   For now, the values of ```SENTRY_SDK_DSN, CPCS_DATA_ACCESS_HASHTAG, CPCS_BASE_URL``` can remain empty.
   
   For local development, you will probably want to use localhost as the postgres and graylog host (although you can use a Dockerized/remote one if you wish!)
   
   ```
   POSTGRES_HOST="localhost"
   GRAYLOG_HOST="localhost"
   ```
4. Create a local DB (or an exposed Docker one, this is up to you)

   Please note that Postgres installation differs from on system, method of installation etc. to another. **This is not bhtom2-specific**, therefore I cannot automatize it fully. Please referto external tutorials and resources, luckily for Postgres there are plenty of them. The important things are to **install Postgres>=14.0**, **create the bhtom2 database and bhtom user** (so, to execute the commands in the init_no_pswd.sql script). Note that the 'pswrd' is not hard-coded, it's the password that you have set up in the .bhtom.env. So if you are executing the lines directly in the console, make sure to pass the appropriate password.
   
   For example, for Mac OS and homebrew you can refer to https://daily-dev-tips.com/posts/installing-postgresql-on-a-mac-with-homebrew/.

   1. Set the .bhtom.env as source of environment variables.
      ```source bhtom2/.bhtom.env```
   2. You can run the Docker/init_no_pswrd.sql script on your local database. In case of any required changes, create a local copy of the script.
      Keep in mind you have to pass the ```$POSTGRES_PASSWORD``` variable as an argument to set the postgres variable ```pswrd```, e.g. (this will works on Linux, but i'm not sure about MacOS):
      ```psql --set=pswrd="$POSTGRES_PASSWORD" -U postgres``` and execute with e.g. ```\i Docker/init_no_pswrd.sql```
      Another method would be to just log in to the ```psql``` console and copying the script lines. But then you have to substitute ```pswrd``` with the password from .bhtom.env

   3. Remember to fill the necessary values in the .bhtom.env file.
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

Add superuser:

``docker-compose run web python manage.py createsuperuser``

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

- When testing, you might encounter a problem:

```Got an error recreating the test database: must be owner of database test_bhtom2```

if you are working on a local database, perhaps you can just set bhtom as a superuser...

```ALTER USER bhtom WITH SUPERUSER;```

- Some users experienced postgresql unable to find some libraries (dylib.so) when launching via entrypoint.sh. One fix we found was to make sure ```psycopg2``` and ```psycopg2-binary``` are uninstalled via pip, and then ```psycopg2-binary``` installed via conda:

```conda install -c conda-forge psycopg2-binary```
