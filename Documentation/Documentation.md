
# BHTOM2 Documentation

Click [here for BHTOM2 API documentation](DocumentationAPI.md).


**Note: the documentation is still in preparation.**

In the meantime, you can listen to [a recording on the BHTOM2 presentation by Lukasz Wyrzykowski from Malta 2023 workshop](https://www.youtube.com/watch?v=jzlkFjEZVz0)

# 1. Brokers

Brokers in BHTOM search for time-series archival data in photometric (and soon also radio and spectra) archives providing publicly available data.

### Gaia Alerts
Webpage: https://gsaweb.ast.cam.ac.uk/alerts

### Gaia DR3 lightcurves
Oficial Gaia DR3 data release. Limited to selected sources only.

### NEOWISE and ALLWISE
ALLWISE is an archival MID-IR WISE data, while NEOWISE is a new on-going scanning mission, providing data every 6 months for targets from all-over the sky

### CRTS (Catalina)
Read directly from Caltech archive, contain neary 10-year long time-series for most of the sky (North and South) except the Galactic Plane. Observations were taken in a broad-band clear filter we call CRTS (CL)

### FIRST (Radio)
Reads WSDB archive. WSDB is a vast database of archival surveys stored and maintained at the Institute of Cambridge, UK, by Sergey Koposov.

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


<!-- # AAVSO

URL for fetching AAVSO data is set in settings.py: AAVSO_API_PATH: str = 'https://www.aavso.org/vsx/index.php'

AAVSO name is set as a TargetExtra tag at target create with aavso_name = name by default. Later can be changed.  -->

### CPCS
Old service, Cambridge Photometric Calibration Server, now used only as a repository of old observations prior to BHTOM2. 

### ASASSN (ASAS-SN)
As of 2023, there are three sources of ASASSN photometry: variable star catalogue, pre-computed photometry and photometry on request (most fresh data). Because of that, the ASASSN URL for a Target has to be the full path to the URL with the object. First, the user has to manually identify the object in ASASSN SkyPatrol db by entering coordinates (https://asas-sn.osu.edu/), then select one of the three paths there, one the webpage with the object and copy its URL as the ASASSN url, for example, https://asas-sn.osu.edu/photometry/31a0bd00-3b2c-541b-9bb6-1a3bf050da34. The only exception is for variable, where for the name the user has to copy the link to the CSV file, e.g. 
for variable star https://asas-sn.osu.edu/variables/448970 it is going to be https://asas-sn.osu.edu/photometry/31a0bd00-3b2c-541b-9bb6-1a3bf050da34.csv.
For the ASASSN name one can use either the name found in ASASSN archive, or a generic ASASSN+Ra+Dec name.

### ATLAS
The time-series data has to be added manually by requesting data from ATLAS Webpage: https://fallingstar-data.com/forcedphot/.
Make sure you request for photometry with reference flux added: from here https://fallingstar-data.com/forcedphot/queue/, marking **Use reduced (input) instead of difference images.**. Under ATLAS url the user should put the entire link to the photometry, e.g. https://fallingstar-data.com/forcedphot/static/results/job664347.txt For the name, one can use simply a generic name ATLAS+RA+DEC.



