# BHTOM - Black Hole Target Observation Manager

## Overview

BHTOM (Black Hole Target Observation Manager) is an advanced web-based system designed to manage time-domain observations for a network of telescopes. It facilitates data collection, processing, and analysis of astronomical observations. BHTOM is built on top of a scalable architecture that supports integration with multiple services like CPCS, Upload, and Harvester to provide a comprehensive solution for researchers, telescope operators, and students.

## Key Features

- **Telescope Network Coordination**: BHTOM allows users to manage and coordinate observations from a network of telescopes.
- **Data Processing and Calibration**: Handles the upload and calibration of photometric and FITS data through integration with CPCS.
- **Archiving and Analysis**: Efficiently stores and processes large volumes of time-domain data, enabling advanced analysis.
- **Automated Workflows**: Supports automation of data workflows, including target submission, data calibration, and result visualization.

## Architecture

The BHTOM system is divided into several microservices:

- **CPCS**: Handles data calibration, archiving, and integration with external databases.
- **Harvester**: Gathers photometric data from external sources and integrates it into the BHTOM database.
- **Upload Service**: Manages the submission and processing of photometric and FITS data from users.
- **Core BHTOM Services**: Manages user accounts, proposals, requests, and overall coordination of the observation process.

For more detailed information, please refer to the [Architecture Documentation](./architecture.md).

## Installation

### Prerequisites

Before installing BHTOM, make sure you have the following:

- Python 3.9+
- PostgreSQL 14+
- Kafka
- Docker (optional for containerized deployment)

### Setup Instructions

1. Clone the BHTOM repository:

   X
   git clone https://github.com/BHTOM-Team/bhtom2.git
   cd bhtom2
   X

2. Initialize and update submodules:

   X
   git submodule update --init --recursive
   X

3. Follow the installation instructions for each component:
   - [CPCS](../cpcs/README.md)
   - [Harvester](../harvester/README.md)
   - [Upload Service](../upload/README.md)

4. Start the services locally using Docker or a local environment.

For detailed installation instructions, see the [Installation Documentation](./installation.md).

## Usage

BHTOM provides a user-friendly web interface and API for managing observation targets, submitting data, and retrieving results. Users can:

- Add new targets for observation.
- Upload data and track its processing status.
- Retrieve calibrated photometric data for analysis.
- Integrate with custom scripts through the BHTOM API.

Visit the BHTOM web portal or use the API documentation for more details.

## API Documentation

The BHTOM API allows for programmatic access to all features of the system, including target management, data uploads, and result retrieval. The API can be used to automate workflows and integrate with external tools.

For more information, see the [API Documentation](./DocumentationAPI.md).

## Contributing

Contributions to BHTOM are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new feature branch.
3. Submit a pull request for review.

For detailed guidelines, see the `CONTRIBUTING.md` file.

## License

BHTOM is licensed under the MIT License. See the `LICENSE` file for more details.

## Troubleshooting

- **Database Issues**: Verify PostgreSQL settings in the `.env` file.
- **Submodule Errors**: Run `git submodule update --init --recursive` to ensure all submodules are up to date.
- **Service Failures**: Check Docker logs or local server logs for error messages.

For more troubleshooting tips, see the [Troubleshooting Section](./installation.md#troubleshooting).

## Support

For any questions or support requests, please open an issue on the GitHub repository or contact the BHTOM team through the web portal.

