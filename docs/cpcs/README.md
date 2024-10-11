# CPCS - Calibration and Photometry Control Service

## Overview

CPCS (Calibration and Photometry Control Service) is a core component of the BHTOM ecosystem. It handles the calibration, plotting, and archiving of photometric data, enabling accurate and consistent data processing for time-domain astronomy.

## Features

- **Calibration**: Automatically calibrates incoming photometric data against standardized references like Gaia DR3.
- **Archive Management**: Stores photometric data and allows retrieval of historical data for further analysis.
- **Chart Generation**: Creates plots and visualizations of photometric observations for easy data interpretation.
- **WSDB Cache Integration**: Leverages the WSDB Cache to store and retrieve large datasets efficiently.

## Installation

### Prerequisites

Before installing CPCS, ensure that you have the following installed:
- Python 3.9+
- PostgreSQL
- Kafka

### Steps

1. Clone the repository:
    ```bash
    git clone https://github.com/BHTOM-Team/cpcsv2.git
    cd cpcsv2
    ```

2. Create a virtual environment (recommended):
    ```bash
    conda create -n cpcs python=3.9
    conda activate cpcs
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file from the template:
    ```bash
    cp template.env .env
    ```

5. Set up the PostgreSQL database:
    - Create a database and user for CPCS.
    - Update the `.env` file with the correct database connection details.

6. Run migrations:
    ```bash
    python manage.py migrate
    ```

## Usage

To start the CPCS service locally, run:
```bash
python manage.py runserver
```

This will start the service on `http://localhost:8000`.

## API Endpoints

CPCS provides the following key API endpoints for integration with other services:

- **/calibrate**: Endpoint for calibrating photometric data.
- **/archive**: Access archived photometric data.
- **/generate-charts**: Generate visualizations of data.
- **/wsdb-cache**: Retrieve data from WSDB cache for efficient data processing.

## Troubleshooting

- Ensure that all environment variables in the `.env` file are correctly set.
- If you encounter database connection issues, verify your PostgreSQL configuration and credentials.
- For issues with Kafka, make sure the Kafka service is running and accessible.

## Contributing

Contributions to CPCS are welcome. Please fork the repository and submit a pull request for review.

## License

CPCS is licensed under the MIT License. See the `LICENSE` file for more details.
