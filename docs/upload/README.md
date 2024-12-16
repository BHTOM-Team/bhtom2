# Upload Service

## Overview

The Upload service in BHTOM is responsible for handling the upload of photometric files and FITS data from users. It processes the uploaded data, performs necessary calibrations, and integrates the results into the BHTOM database. This service is essential for managing large-scale data uploads and ensuring that all data is properly calibrated and stored.

## Features

- **File Uploads**: Accepts photometric files and FITS data from users.
- **Data Calibration**: Automatically calibrates uploaded photometric data.
- **Integration with CPCS**: Passes calibrated data to the CPCS for further processing and archiving.
- **Supports Large Data Volumes**: Efficiently handles bulk uploads from users.

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL
- Kafka
- Docker (optional for containerized deployment)

### Local Setup

1. Clone the repository:

   ```
   git clone https://github.com/BHTOM-Team/upload-service.git
   cd upload-service
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

## API Endpoints

Key API endpoints provided by the Upload service:

- **/upload-photometry**: Endpoint for uploading photometric data files.
- **/upload-fits**: Endpoint for uploading FITS files.
- **/calibrate**: Endpoint for manually triggering data calibration.
- **/status**: Check the status of uploaded files and their processing state.

## Usage

The Upload service is used to manage the submission and processing of photometric and FITS data. To upload a file, use:

   ```
   curl -X POST -F "file=@path/to/your/file.fits" http://localhost:8000/upload-fits
   ```

This will initiate the upload and processing of the provided FITS file.

## Troubleshooting

- **File Upload Failures**: Ensure that your file is in the correct format and that the server is running.
- **Database Connectivity**: Verify PostgreSQL settings in the `.env` file.
- **Kafka Issues**: Make sure Kafka is running and properly configured.
- **Calibration Errors**: If calibration fails, check the data format and integrity of the uploaded files.

## Contributing

Contributions to the Upload service are welcome. Fork the repository and open a pull request with your changes.

## License

The Upload service is licensed under the MIT License. See the `LICENSE` file for more details.
