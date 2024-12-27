# BHTOM Architecture

## Overview

The BHTOM (Black Hole Target Observation Manager) system is designed to manage astronomical observations, coordinate a network of telescopes, and process time-domain data. Its architecture integrates various components to ensure efficient data handling, real-time processing, and seamless coordination among researchers, telescope operators, and data storage systems.

## Key Components

### 1. **BHTOM DB**

- **Description**: The core database of the BHTOM system, adapted from the TOM Toolkit with minor customizations.
- **Purpose**: Stores data related to targets, observations, and user information.
- **Technology**: Uses PostgreSQL for reliable data storage and query handling.
- **Functionality**: Supports various operations such as managing target data, user-generated observations, and handling requests for data retrieval.

### 2. **WSDB Cache DB**

- **Description**: A specialized database for caching data from external sources like WSDB Cambridge.
- **Purpose**: Ensures efficient retrieval of archived data, reducing the load on primary data sources.
- **Key Features**:
  - Uses `q3c` for fast spatial queries.
  - Archives data from BHTOM1 for historical reference.
  - Plans for future integration of photometry catalogs.

### 3. **CPCS (Cambridge Photometric Calibration Server)**

- **Description**: A crucial component for data calibration and standardization.
- **Purpose**: Processes uploaded photometric data, applies calibrations, and generates standardized outputs.
- **Functionality**:
  - Supports calibration with reference data from Gaia_DR3.
  - Generates plots for visual analysis.
  - Manages a cache of WSDB data for rapid access.
- **Data Flow**:
  - Retrieves calibration data from the WSDB cache.
  - Stores calibration results in BHTOM DB for easy access.

### 4. **Kafka**

- **Description**: A distributed messaging system used to connect various components of BHTOM.
- **Purpose**: Manages data streams between services for real-time processing and communication.
- **Key Features**:
  - High throughput and low latency for handling large volumes of observation data.
  - Scalable and resilient to ensure continuous data flow.
  - Used for both uploading photometric data and processing observation requests.
- **Topics**:
  - `Event_Calibration_File`
  - `Event_Create_Target`
  - `Event_Reduced_Datum_Update`
- **Infrastructure**:
  - 3 Kafka Brokers for message distribution.
  - 3 Zookeeper instances for managing Kafka clusters.

### 5. **Upload Service**

- **Description**: Handles the upload of photometric data files and raw observations.
- **Purpose**: Ensures that data from various telescopes can be efficiently ingested into the BHTOM system.
- **Functionality**:
  - Receives FITS files and instrumental photometry.
  - Uses Kafka to forward data to CPCS for calibration.
  - Stores results and updates BHTOM DB.
- **Data Flow**:
  - User uploads files via the API.
  - Upload service sends data to Kafka, then CPCS processes it.
  - Calibrated data is stored in BHTOM DB and displayed to users.

### 6. **Microservices Architecture**

- **Description**: BHTOM follows a microservices architecture for modularity and scalability.
- **Components**:
  - **BHTOM Base**: The core server handling the main functionalities.
  - **CPCS**: For photometric calibrations.
  - **Harvester Services**: Automates data gathering from various sources like Gaia Alerts, ZTF, and NEOWISE.
  - **CCDPhotService**: A dedicated service for handling photometry results.
  - **Graylog and Elasticsearch**: Integrated for centralized logging and data search, ensuring that logs from all services are easily accessible.
- **Benefits**:
  - Enables independent development and scaling of each component.
  - Reduces deployment complexity through the use of Docker.


## Observations and Data Management

- **Observation Portal**: Manages user accounts, proposals, and observation requests.
- **Downtime Database**: Keeps track of planned downtimes for telescopes, optimizing observation schedules.
- **Adaptive Scheduler**: Integrates with CPCS to optimize observation requests, adjusting schedules based on telescope availability and data priorities.

## Summary

The BHTOM architecture is designed to handle large-scale astronomical observations with high efficiency. Its modular components allow easy updates and scalability, ensuring that new telescopes and observation sources can be integrated seamlessly. With tools like Kafka and CPCS, it provides a robust solution for real-time data management, processing, and collaboration among the global research community.
