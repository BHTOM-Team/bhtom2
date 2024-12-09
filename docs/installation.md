# Installation

This document provides detailed steps for setting up the BHTOM system on your local machine or deploying it in a production environment.

---

## Prerequisites

Before installing the system, ensure the following dependencies are installed:

- **Python**: Version 3.9 or newer.
- **PostgreSQL**: Version 14 or newer.
- **Docker and Docker Compose**: Ensure Docker Compose version is at least 1.25.0.
- **Kafka**: A running Kafka service is required for some services.

---

## Local Development (Without Docker)

### Step 1: Clone the Repository

Clone the main BHTOM repository and its submodules:

```
git clone https://github.com/BHTOM-Team/bhtom2.git
cd bhtom2
git submodule foreach --recursive git reset --hard
git submodule update --init --recursive --remote
```

### Step 2: Create a Conda Environment

```
conda create -n bhtom2 python=3.9
conda activate bhtom2
conda install pip
```

### Step 3: Install Requirements

```
pip install -r requirements.txt
```

### Step 4: Configure the Environment

Copy the environment template and fill in necessary values:

```
cp template.env bhtom2/.bhtom.env
```

Update `.bhtom.env` with database and other configuration details.

### Step 5: Set Up the Database

Ensure PostgreSQL is installed. Create a user and database:

```
psql --set=pswrd="YOUR_PASSWORD" -U postgres -c "CREATE USER bhtom WITH PASSWORD 'YOUR_PASSWORD';"
psql --set=pswrd="YOUR_PASSWORD" -U postgres -c "CREATE DATABASE bhtom2 OWNER bhtom;"
```

Run the `init_no_pswrd.sql` script to initialize the database.

### Step 6: Run the Development Server

```
python manage.py runserver
```

---

## Using Docker for Development

### Step 1: Create the `.env` File

```
cp template.env bhtom2/.bhtom.env
```

Fill in the required values.

### Step 2: Start the Docker Containers

```
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --build
```

---

## Running Tests

To run the tests:

1. Ensure your `.bhtom.env` file is correctly configured.
2. Run the following command:

```
python manage.py test
```

---

## Troubleshooting

- Ensure you have the latest PostgreSQL version installed.
- Verify that all environment variables in `.bhtom.env` are set correctly.
- Check that Kafka is running and accessible.
- If encountering database permissions errors, ensure the `bhtom` user has `CREATEDB` privileges.
- To fix permission issues on Unix systems:

```
chmod +x dev_entrypoint.sh
```

For further support, refer to the project’s main documentation.
