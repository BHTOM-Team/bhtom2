# BHTOM2 Documentation

Click [here for BHTOM2 API documentation](https://github.com/BHTOM-Team/bhtom2/blob/bhtom2-dev/Documentation/DocumentationAPI.md).
Click [here for BHTOM2 instalation documentation](https://github.com/BHTOM-Team/bhtom2/blob/bhtom2-dev/Documentation/installation/local_installation_docker.md).

We strongly recommend running BHTOM2 using Docker to streamline the setup process and ensure a consistent and simplified experience. Docker eliminates many potential configuration issues, making it easier to get started quickly and focus on using BHTOM2 without worrying about environment-specific dependencies.

**The visual manual from December 2024 in form of a pdf is available [here](https://github.com/BHTOM-Team/bhtom2/blob/bhtom2-dev/Documentation/2024.12-BHTOM2-Manual.pdf)**

**Note: the documentation is still in preparation.**

The recordings on talks on BHTOM and related topics from [the 15th Gaia Science Alerts workshop in Crete 2024 can be found here](https://www.youtube.com/playlist?list=PLfl-CrV1b39ar0hXTHpT7r8cnnx_FU2DM)

You can also listen to [a recording on the BHTOM2 presentation by Lukasz Wyrzykowski from Malta 2023 workshop](https://www.youtube.com/watch?v=jzlkFjEZVz0)


## Overview

BHTOM (Black Hole Target Observation Manager) is an advanced web-based system designed to manage time-domain observations for a network of telescopes. It facilitates data collection, processing, and analysis of astronomical observations. BHTOM is built on top of a scalable architecture that supports integration with multiple services like CPCS, Upload, and Harvester to provide a comprehensive solution for researchers, telescope operators, and students.

## Key Features

- **Telescope Network Coordination**: BHTOM allows users to manage and coordinate observations from a network of telescopes.
- **Data Processing and Calibration**: Handles the upload and calibration of photometric and FITS data through integration with CPCS.
- **Archiving and Analysis**: Efficiently stores and processes large volumes of time-domain data, enabling advanced analysis.
- **Automated Workflows**: Supports automation of data workflows, including target submission, data calibration, and result visualization.

## Architecture

The BHTOM system is divided into several microservices:

- **CPCS**: Performs calibration of photometric files and generates data visualizations and charts.
- **Harvester**: Gathers photometric data from external sources and integrates it into the BHTOM database.
- **CCDPHOT**: Manages user accounts, proposals, requests, and overall coordination of the observation process.
- **Upload Service**: Manages the submission and processing of photometric and FITS data from users.
- **Core BHTOM Services**: Manages user accounts, proposals, requests, and overall coordination of the observation process.

For more detailed information, please refer to the [Architecture Documentation](./architecture/architecture.md).


## Usage

BHTOM provides a user-friendly web interface and API for managing observation targets, submitting data, and retrieving results. Users can:

- Add new targets for observation.
- Upload data and track its processing status.
- Retrieve calibrated photometric data for analysis.
- Integrate with custom scripts through the BHTOM API.

Visit the BHTOM web portal or use the API documentation for more details.


# 1. Time-Domain Archives

Brokers in BHTOM search for time-series archival data in photometric (and soon also radio and spectra) archives providing publicly available data. We access the data either via API's provided by each service, or we access copies of archives stored in the Whole Sky Data Base (WSDB), maintained at the Institute of Cambridge, UK, by Sergey Koposov.

### Gaia Alerts
Webpage: https://gsaweb.ast.cam.ac.uk/alerts

### Gaia DR3 lightcurves
Oficial Gaia DR3 data release. Limited to selected sources only.

### NEOWISE and ALLWISE
ALLWISE is an archival MID-IR WISE data, while NEOWISE is a new on-going scanning mission, providing data every 6 months for targets from all-over the sky

### CRTS (Catalina)
Read directly from Caltech archive, contain neary 10-year long time-series for most of the sky (North and South) except the Galactic Plane. Observations were taken in a broad-band clear filter we call CRTS (CL)

### FIRST (Radio)
From WSDB.

Problem: only mean epoch JD is stored in that table. 
Returns flux in miliJanskys (ReducedDatumUnit.MILLIJANSKY).
Filter name: FIRST(Flux 1.4GHz)

### ZTF/ANTARES

ZTF data is read from most recent Data Release and ANTARES broker (newest data). 

### SDSS 
Reads WSDB archive, DR14 is read,  typically 1 observation per filter per epoch, but for targets from e.g. Stripe82 there are way more epochs. 

### PANSTARRS (PS1)

WSDB is read for typically single epochs in multiple bands.

### LINEAR

Uses WSDB. About 10 years-long timeseries in a clear filter we call LINEAR(CL).



### CPCS
Old service, Cambridge Photometric Calibration Server, now used only as a repository of old observations prior to BHTOM2. 

### ASASSN (ASAS-SN)
ASAS-SN broker uses ASAS-SN's Skyportal (http://asas-sn.ifa.hawaii.edu/documentation/getting_started.html) to identify ASAS-SN id and extract the photometry. Additionally, we query the table with ASAS-SN transients (https://www.astronomy.ohio-state.edu/asassn/transients.html) to identify alerts with ASAS-SN name. The search radius is 7 arcsec.

### ATLAS
The data from this Survey orignate from ATLAS Webpage: https://fallingstar-data.com/forcedphot/.
For a new target created, the request is sent to this service. It typically takes up to 15 minutes for the request on the entire ATLAS time-span to be generated. The data are then automatically loaded to the target. Then, an automated process is taking care to keep ATLAS light curve up-to-date, with refresh time of 12h. Note, we download magnitudes which include reference flux (if available).


ATLAS data is automatically cleaned from extreme outliers (scipy.stats.z_score>10) as well as limited to 5>mag>22, including negative magnitudes (limits), which are not currently stored nor showed.

Cite: Tonry et al. (2018), Smith et al. (2020), Heinze et al. (2018), Shingles et al. (2021).



