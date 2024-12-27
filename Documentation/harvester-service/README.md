# Harvester Service

## Overview

The Harvester service is responsible for aggregating data from various astronomical sources and integrating them into the BHTOM system. It automates the process of fetching, parsing, and storing time-domain data to support astronomical research and observation management.

## Features

- **Automated Data Harvesting**: Pulls data from various astronomical data sources.
- **Data Standardization**: Converts raw data into a standardized format for easy integration into BHTOM.
- **Supports Multiple Sources**: Can integrate with different astronomical catalogs and databases.
- **Scheduler Integration**: Uses cron jobs or task schedulers to automate data fetching.

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL
- Kafka
- Docker (optional for containerized deployment)

### Local Setup

1. Clone the repository:

   ```
   git clone https://github.com/BHTOM-Team/harvester.git
   cd harvester
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up the environment variables by creating a `.env` file:

   ```
   cp template.env .env
   ```

5. Run migrations to set up the database:

   ```
   python manage.py migrate
   ```

6. Start the service:

   ```
   python manage.py runserver
   ```

The service will start on `http://localhost:8000`.


## Troubleshooting

- **Database Issues**: Make sure your PostgreSQL instance is running and the database connection details in `.env` are correct.
- **Kafka Connectivity**: Verify that the Kafka service is accessible and the necessary topics are configured.
- **Scheduler Issues**: If automated tasks are not running, check your cron job or task scheduler settings.


## License

The Harvester service is licensed under the MIT License. See the `LICENSE` file for more details.
