# Architecture of BHTOM

## Overview

The BHTOM (Black Hole Target Observation Manager) system is built using a combination of Python libraries, Django web applications, and other components that enable the coordination of telescope networks and management of astronomical observations. This document outlines the key architectural components and how they work together to facilitate data processing and observation management.

## Core Components

### 1. Observation Portal
   - The **Observation Portal** is the heart of BHTOM, managing user accounts, observation proposals, requests, and scheduling of observations.
   - It serves as a database and API for handling observation data and provides a user-friendly interface for researchers, telescope operators, and students.

### 2. Configuration Database (ConfigDB)
   - The **ConfigDB** manages detailed information about the observatory setup, such as site structure, telescope configurations, and instrument settings.
   - It enables automatic validation and auto-completion of data when adding or modifying telescope and instrument details, ensuring accuracy in observations.

### 3. WSDB Cache Database
   - Uses `q3c` for efficient spatial queries.
   - Caches data from WSDB Cambridge to reduce load and speed up access for subsequent queries.
   - Stores archived data from BHTOM1 and plans to include photometric catalogs in the future.

## Optional Components

### 1. Adaptive Scheduler
   - The **Adaptive Scheduler** processes observation requests and prioritizes them to generate a schedule for telescope observations.
   - While tightly integrated into the BHTOM ecosystem, users can also opt for custom scheduling solutions if needed.

### 2. Science Archive and Ingester
   - Provides the means to store image metadata and links to observation data files, using AWS S3 for scalable storage.
   - This archive enables users to search, filter, and download data products, supporting long-term data storage and analysis.

### 3. Downtime Database
   - Manages periods of scheduled downtime for telescopes and instruments.
   - Helps improve scheduling efficiency by ensuring observations are planned around known downtime intervals.

## Data Flow

### 1. Upload Photometry Files
   - Users can upload photometry files directly through the **Upload Service**.
   - The data is processed through Kafka to CPCS (Calibration, Plot Generation, and Data Update) before being saved in the BHTOM database.
   - Users can access the processed results via the BHTOM portal.

### 2. Upload FITS Files
   - FITS files are handled by the **Upload Service**, processed using **Dramatiq** for asynchronous task handling, and further calibrated through **CCDPhotSvc**.
   - Results are then stored back into the BHTOM database and presented to users for analysis.

## Kafka Integration

### 1. Event Handling
   - Kafka manages events such as `Event_Calibration_File`, `Event_Create_Target`, and `Event_Reduced_Datum_Update` to streamline the flow of observation data.
   - This helps in maintaining the high throughput needed for real-time data ingestion and processing.

### 2. Infrastructure
   - BHTOM utilizes a Kafka cluster with three brokers and three Zookeeper instances to ensure data consistency and reliability.
   - The system also includes a Kafka UI for monitoring and managing topics and brokers.

## Docker-based Microservices

### 1. Containerized Environment
   - All BHTOM services run in **Docker containers**, allowing for easy deployment and scaling.
   - Services include:
     - `kafka`
     - `mongo`
     - `wsdb`
     - `upload-service`
     - `graylog` for centralized log management
   - Containers share access to a common disk for data persistence.

### 2. Graylog and Elasticsearch
   - **Graylog** is used to centralize log collection from various services.
   - **Elasticsearch** is used for indexing logs and providing quick access to diagnostic data.

## Diagrams and Visualizations

For a visual representation of the BHTOM architecture, refer to the diagram below:

![BHTOM Architecture Diagram](link-to-diagram.png)
