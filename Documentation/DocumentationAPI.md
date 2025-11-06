
# BHTOM2 API Documentation

## Introduction

This is a simple guide for BHTOM's REST API. It lets you use BHTOM webpage features in your own programs. You can get a list of targets, add observations, download data and more. Let's get started!

> **Remember!** To use API you should get your own TOKEN first!

# AUTHORIZATION API: /api/token-auth/

### Description
<!-- 
## Token-Auth API -->

The `token-auth` API provides a method for users to obtain an **authentication token** by submitting their `username` and `password`. 
Once you have acquired this token, it allows you to access and utilize all other available APIs.

### Endpoint

- **Method**: POST
- **URL**: `/api/token-auth/`

### Request Parameters

- `username` (string, required): User's username for authentication.
- `password` (string, required): User's password for authentication.

### Example Request

```http
curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/api/token-auth/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
  "username": "username",
  "password": "password"
}'
```

### Response
    The API responds with an authentication token in JSON format if the provided username and password are valid.
#### Example Response:
    {
    "token": "abc123def456"
    }


# DATA UPLOAD API

### Description
This API facilitates programmable batch file uploads to the **BHTOM system**. It offers a command-line interface for uploading files along with their associated meta data.

<!-- Please note, an authentication `TOKEN` is required to use this script. -->

### Endpoint

- **Method**: POST
- **URL**: `/upload`

### Usage

The ready-to-use script is located in the `documentation_scripts` folder. please fill parameters in the script before use

```bash
python upload_files_script.py  
```

### Arguments
Note you can hardcode some of the recurring arguments within the script, for example token, observatory

- `--directory` : The directory containing all the necessary fits files
or
- `--filename` : A single file to be processed

- `--token token`: authentication token for the BHTOM user, which will be associated to the data points uploaded
- `--target target`: Target destination for the uploaded files
- `--observatory_name observatory`: ONAME (prefix name of observatory/camera)

<!-- - `<files>`: Comma-separated list of files to be uploaded -->
<!-- TODO: LW: check photometry vs SExtractor, we need both: WILL BE ADDED -->
### Optional Arguments

<!-- - `--match_dist <match_dist>`: This sets the matching distance (float) for astrometric cross-match in the standardisation procedure.  -->
<!-- LW: I hid the match_dist as we set it fixed -->
- `--data_product_type data_product_type`: Type of data product: `fits_file`, `photometry` (instrumental in SExtractor format), `photometry_csv` or `spectroscopy`
- `--comment comment`: comment to your upload
- `--dry_run True/False`: if true, the script will be run in Dry Run (test) mode. The data will processed but will not be stored in the database. The default is false.
<!-- - `--no_plot`: if true, no calibration plot will be generated. The default setting is false. -->
- `--mjd <mjd>`: Modified Julian Date (float) [note MJD=JD-2400000.5], required for single photometry file
- `--observers [observers]`: List of observers names to set as observers, observer name it is a username and is case sensitive

- `--match_dist <match_dist>`: Matching Radius in arcsec (do not set if you want to run on auto).

**Note on Matching Radius**: This value indicates how accurate is your astrometry on your image. We perform a cross-match between objects from your image and Gaia catalogue with 5 arcsec very generous matching radius, but then we remove bad matches. This also helps us determine the accuracy of your astrometry. The standard deviation of the match in RA and Dec is then used as a matching dist (if in auto mode). This value is used solely in one place - when we identify the desired target among your objects. If the target is not found within the matching radius (it was either further away than the matching radius, or too faint), the outcome of the calibration is the Limit (with mag.error=-1). The limiting magnitude is computed based on the faintest object seen on your frame.


### Example Usage 1

```bash
python upload_files_script.py --token 123_my_user_name_token_456 --observatory_name"my telescope" --target Gaia22bpl --directory path_to_files/
```

### Example Usage 2

```bash
python upload_files_script.py --token 123token456 --target Gaia22bpl --observatory "my telescope" --data_product_type photometry --filename file1.cat --mjd 51234.123 --observer "John Doe"
```

### Example Usage 3 for photometry CSV file in Python notebook

```
headers={
            'Authorization': "Token " + str(auth_token)
        }

data = {
    'target': 'AT2025abju',
    'data_product_type': 'photometry_csv',
    'observatory': 'GOTO',
    'observers': 'wyrzykow',
    'comment': 'Data from TNS'
}
filename="/content/phot_test.csv"
file_list = [filename]

response = requests.post(
    url='https://uploadsvc2.astrolabs.pl/upload/',
    headers=headers,
    data=data,
    files={'files': open(filename, 'rb')}
)
```

Note, the observers field has to be valid user names registered in BHTOM (it can be a list). The owner of the datapoints submitted this way will still be the user behind the authorisation token used. Non-detections (limits) can be denoted with negative mag error.

### Response

The script will display the response from the API with a list of uploaded files with id of each file, so you can check the calibrations result by their ids.

### Dependencies

- Python 3.x
- The `requests` library (install with `pip install requests`)


# CALIBRATION FILE UPLOAD API

### Description
This API facilitates programmable batch file calibration file to the **BHTOM system**. It offers a command-line interface for uploading files along with their associated meta data.

<!-- Please note, an authentication `TOKEN` is required to use this script. -->

### Endpoint

- **Method**: POST
- **URL**: `/calibFile`


### Request Headers

- `accept: application/json`: Specify the desired response format as JSON.
- `Authorization: Token 10f21fe7308f06f7e23ccb7848da554c2271be49`: Authentication token for the API.
- `Content-Type: application/json`: Specify the format of the request payload as JSON.
- `X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr`: CSRF token for security.

### Request Body

  -  `photometry_file `: TYPE_FILE
  -  `ra`: FORMAT_FLOAT
  -  `dec`: FORMAT_FLOAT
  -  `match_dist`: FORMAT_FLOAT
  -  `survey`: TYPE_STRING
  -  `filter`: TYPE_STRING
  -  `no_plot`: TYPE_BOOLEAN
  -  `image_format`: TYPE_STRING

### Example Request

```bash
curl -X 'POST' \
  'https://uploadsvc2.astrolabs.pl/calibFile/' \
  -H 'accept: application/json' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
        photmetry_file = 'file.dat'
        ra =  1.23
        dec = 4.56
        match_dist = 2.0
        no_plot = True
        survey = 'GaiaSp'
        filter = 'V'
        image_format = 'png'
  }'
```
### Response

The script will display the response from the API with a calibration result, so you can check the calibrations result and plot.

# CALIBRATIONS API

<!-- ### Description -->

<!-- This Python script allows you to retrieve a list of catalogues from the BHTOM2 system using the `get_catalogs` API. It provides a command-line interface for making GET requests with proper authorization. API returns 200 records by request, use parametr "page" to get more-->

<!-- TOKEN is required! -->
<!-- 
### Endpoint

- **Method**: GET
- **URL**: `/calibration/get-catalogs/?page=1`

## Usage

```bash
python get_catalogs_script.py <token>


### Arguments

<token>: Authentication token.

### Example Usage

python get_catalogs_script.py abc123 1

### Response

The script will make a GET request to the API and display the list of available catalogs, including their IDs, names.

### Dependencies

Python 3.x
The requests library (install with pip install requests)

--- -->


### Description
 <!-- /calibration/get-calibration-res/ -->

This API endpoint allows users to retrieve calibration results for previously uploaded observations. For 1 request you can get only 200 records, if you want more - use "page" in request to get other records.

<!-- TOKEN is required! -->

### Request

- **Method**: POST
- **URL**: `/calibration/get-calibration-res`

### Request Headers

- `accept: application/json`: Specify the desired response format as JSON.
- `Authorization: Token <your token>`: Authentication token for the API.
- `Content-Type: application/json`: Specify the format of the request payload as JSON.
- `X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr`: CSRF token for security.

### Request Body

- `filename` (array, required): Array containing files name for calibration
- `calibid` (array, required): Array containing files ID for calibration
- `getPlot` (boolean): Flag to indicate whether to retrieve the calibration plot (for python: True/False, for curl true/false) 
- `page` (integer): The number of page 
### Example Request

```bash
curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/calibration/get-calibration-res/' \
  -H 'accept: application/json' \
  -H 'Authorization: Token <your token>'\
  -H 'Content-Type: application/json' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
    "filename": ['296_cat-Gaia19eyy-ROAD-not-matched','other_file_name_without_extension'],
    "calibid": [1234, 23212, 12345],
    "getPlot": true,
    "page": 2
  }'
```
    You can use script as well

```bash
    python get_calib_res.py "yourToken" 1 "2_photometry_sample_2" 2 --get_plot
```
### Response

    Response is the list with calibration result and plot(if getPlot=True) for each file id 


# OBSERVATORY API

## 1. Observatory List
<!-- /observatory/getObservatoryList/ -->
    
    This API endpoint allows users to get the list of observatories registered in the system. You can get 200 record per one request, use "page" to get more records

    <!-- TOKEN is required! -->

### Request

- **Method**: POST
- **URL**: `observatory/getObservatoryList/`

### Parameters

- `name` (string): A parameter for specifying a name.
- `lon` (number): Longitude value.
- `lat` (number): Latitude value.
- `active_flg` (boolean): A flag to indicate whether an item is active.
- `created_start` (string): A date and time parameter for specifying a start date.
- `created_end` (string): A date and time parameter for specifying an end date.
- `page` (number): The number of requested page.


### Example Request Body (Optional)

```json
{
  "name": "Example Name",
  "lon": 123.456,
  "lat": 45.678,
  "active_flg": true,
  "created_start": "2023-09-01T12:00:00Z",
  "created_end": "2023-09-30T23:59:59Z",
  "page": 1,
}
```

### Request Header

The request header should include the following:

- `Authorization: Token <token>` (required): Authentication token for the API.

### Example Request

```bash
curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/observatory/getObservatoryList/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token <yourToken>' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
  "name": "string",
  "lon": 0,
  "lat": 0,
  "active_flg": true,
  "created_start": "2023-09-28T14:00:09.440Z",
  "created_end": "2023-09-28T14:00:09.440Z",
  "page": 1
}'
```

### Response
    List of registered observatories



## 2. Add Favourite Observatory
<!-- /observatory/addFavouriteObservatory/ -->

This API endpoint allows users to add observatory to their favourite list. Users must provide the (observatory name and camera name) or simply provide oname, and can include an optional comment.

### Request

- **Method**: POST
- **URL**: `observatory/addFavouriteObservatory/`

### Request Headers

- `Authorization: Token <yourToken>` (required): Authentication token for the API.

### Request Body

- `observatory` (string, required): The name of the observatory.
- `camera` (string, required): The name of the observatory camera.
- `comment` (string, optional): An optional comment.
- `oname` ((string, required if observatory or camera is not provided): The short name of observatory/camera ONAME.)

### Example Request Body

```json
{
  "observatory": "Observatory Name",
  "camera": "Camera Name",
  "comment": "This is an optional comment.",
  "oname": "The short name of observatory/camera ONAME"
}
```


### Example Request

#### Use with observatory and camera name:

```bash
curl -X POST \
  'https://bh-tom2.astrolabs.pl/observatory/addFavouriteObservatory/' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -d '{
    "observatory": "Observatory Name",
    "camera": "Camera Name",
    "comment": "This is an optional comment."
  }'
```
#### Or use with ONAME:

```bash
curl -X POST \
  'https://bh-tom2.astrolabs.pl/observatory/addFavouriteObservatory/' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -d '{
    "oname": "ONAME",
    "comment": "This is an optional comment."
  }'
```

## 3. Create Observatory 
<!-- /createObservatory/ -->

    This API allows users to create an observatory. 

### Request

- **Method**: POST
- **URL**: `/observatory/createObservatory/`

### Request Parameters

The request to create an observatory should include the following parameters in the request body:

- `name` (string, required): The name of the observatory.
- `lon` (number, float, required): The longitude coordinate of the observatory.
- `lat` (number, float, required): The latitude coordinate of the observatory.
- `camera_name` -(string, required): The name of the observatory camera.
- `calibration_flg` (boolean, optional): A flag indicating whether the observatory is for calibration purposes only (default is `False`).
- `example_file` (string, optional): An example file associated with the observatory.
- `comment` (string, optional): Additional comments or notes about the observatory.
- `altitude` (number, float, optional): The altitude of the observatory.
- `gain` (number, float, optional): The gain setting of the observatory's equipment.
- `readout_noise` (number, float, optional): The readout noise of the observatory's equipment.
- `binning` (number, float, optional): The binning factor used in observations.
- `saturation_level` (number, float, optional): The saturation level of the equipment.
- `pixel_scale` (number, float, optional): The pixel scale of the observatory's equipment.
- `readout_speed` (number, float, optional): The readout speed of the equipment.
- `pixel_size` (number, float, optional): The pixel size of the equipment.
- `approx_lim_mag` (number, float, optional): The approximate limiting magnitude of the observatory.
- `filters` (string, optional): The filters used in observations.

### Example Request Body

```json
{
    "name": "My Observatory",
    "lon": 45.12345,
    "lat": -120.67890,
    "camera_name": "Camera1",
    "calibration_flg": true,
    "example_file": "observatory_example.txt",
    "comment": "This observatory is for calibration purposes.",
}
```

### Example Requests

You can make requests to create observatories using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Observatory",
    "lon": 45.12345,
    "lat": -120.67890,
    "camera_name": "Camera1",
    "calibration_flg": true,
    "example_file": "observatory_example.txt",
    "comment": "This observatory is for calibration purposes."
  }' \
  https://bh-tom2.astrolabs.pl/observatory/createObservatory/
```

### Using Python Script

You can use a Python script to create observatories:
```bash
python create_observatory.py --name "My Observatory" --lon 45.12345 --lat -120.67890  --camera_name "Camera1" --calibration_flg --example_file "observatory_example.txt" --comment "This observatory is for calibration purposes" --token <yourToken> 
```

## 4. Update Observatory 
<!-- /observatory/update/ -->

    This API allows users to update observatory information. 
### Request

- **Method**: POST
- **URL**: `observatory/updateObservatory/`

### Request Parameters

The request to update an observatory should include the following parameters in the request body:

- `name` (string, required): The name of the observatory.
- `lon` (number, float, optional): The new longitude coordinate of the observatory.
- `lat` (number, float, optional): The new latitude coordinate of the observatory.
- `calibration_flg` (boolean, optional): A flag indicating whether the observatory is for calibration purposes only.
- `comment` (string, optional): New additional comments or notes about the observatory.
- `altitude` (number, float, optional): The new altitude of the observatory.
- `approx_lim_mag` (number, float, optional): The new approximate limiting magnitude of the observatory.
- `filters` (string, optional): The new filters used in observations.

### Example Request Body

```json
{
    "name": "My Observatory",
    "lon": 45.12345,
    "lat": -120.67890,
    "calibration_flg": true,
    "comment": "Updated observatory information."
}
```

### Example Requests

You can make requests to update observatory information using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X PATCH \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Observatory",
    "lon": 45.12345,
    "lat": -120.67890,
    "calibration_flg": true,
    "comment": "Updated observatory information."
  }' \
  https://bh-tom2.astrolabs.pl/observatory/updateObservatory/
```

### Using Python Script

You can use a Python script to update observatory information:

```bash
python create_observatory.py --name "My Observatory" --lon 45.12345 --lat -120.67890 --calibration_flg  --comment "This observatory is for calibration purposes" --token <yourToken> 
```

## 5. Get Favourite Observatory
<!-- /observatory/getFavouriteObservatory/ -->

    This API allows obtaining a favourite observatory.

## Request

- **Method**: POST
- **URL**: `/observatory/getFavouriteObservatory/`

## Request Parameters

You can requested only 200 records per request, use pramater "page" to get more records 
The request to retrieve observatory matrix data can include the following parameters in the request body:

- `user` (string, optional): Filter observatory matrix data by the username of the user associated with the observatory.
- `active_flg` (boolean, optional): Filter observatory matrix data by the active flag, indicating whether the observatory is active.
- `camera` (string, optional): Filter observatory matrix data by the camera name or identifier.
- `created_start` (string, datetime format, optional): Filter observatory matrix data to include only records created on or after the specified date and time.
- `created_end` (string, datetime format, optional): Filter observatory matrix data to include only records created on or before the specified date and time.
-  `page` (number): The number of requested page.

### Example Request Body

```json
{
    "user": "JohnDoe",
    "active_flg": true,
    "camera": "My Camera",
    "created_start": "2023-01-01T00:00:00Z",
    "created_end": "2023-12-31T23:59:59Z"
}
```

### Example Request

You can make a POST request to retrieve observatory matrix data using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "user": "JohnDoe",
    "active_flg": true,
    "camera": "My Camera",
    "created_start": "2023-01-01T00:00:00Z",
    "created_end": "2023-12-31T23:59:59Z"
  }' \
  https://bh-tom2.astrolabs.pl/observatory/getFavouriteObservatory/
```

### Using Python Script

You can use a Python script to retrieve observatory matrix data:

```bash
python get_observatory_matrix.py --user "JohnDoe" --active_flg true --camera "My Camera" --created_start "2023-01-01T00:00:00Z" --created_end "2023-12-31T23:59:59Z" --token <yourToken>
```

## 6. Delete Favourite Observatory
<!-- /observatory/deleteFavouriteObservatory/ -->

    This API allows users to delete favourite observatory records based on the observatory name from their list.
### Request

- **Method**: DELETE
- **URL**: `observatory/deleteFavouriteObservatory/`


### Request Parameters

The request to delete an observatory matrix record should include the following parameter in the request body:

- `observatory` (string, required): The name or identifier of the observatory for which you want to delete the matrix 
- `camera` (string, required): The name or identifier of the observatory camera for which you want to delete the matrix record.

### Example Request Body

```json
{
    "observatory": "My Observatory",
    "camera": "Observatory Camera"
}
```

### Example Request

You can make a DELETE request to delete an observatory matrix record using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X DELETE \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "observatory": "My Observatory",
    "camera": "My Camera"
  }' \
  https://bh-tom2.astrolabs.pl/observatory/deleteFavouriteObservatory/
```

### Using Python Script

You can use a Python script to delete an observatory matrix record:
```bash
python delete_observatory_matrix.py --observatory "My Observatory" --camera "My Camera" --token <yourToken>"
```

# DATA DOWNLOAD API

Here we present end-points how to download the photometry and radio data from BHTOM. 

Please contact us if you plan to use the data in a publication. By downloading the data from BHTOM you agree to follow our data policy and to use this acknowledgment:

```
The data was obtained via [BHTOM](https://bhtom.space), which has received funding from the European Union's Horizon 2020 research and innovation program under grant agreement No. 101004719 (OPTICON-RadioNet Pilot).
```

For more information about acknowledgement and data policy please visit [https://about.bhtom.space](https://about.bhtom.space)


## 1. Photometry download

With this API one can download all photometric observations (magnitudes) in semi-color separated form. The columns of the output are the following: 

***MJD;Magnitude;Error;Facility;Filter;Observer***

### Request 
- **Method**: POST
- **URL**: `/targets/download-photometry/`

### Request Parameters

- `name` (string, required): The name or identifier of the target.

### Example Request Body

```json
{
    "name": "My Target",
}
```

### Example Request

You can make a POST request to download the data using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "name": "My Target",
  }' \
  https://bh-tom2.astrolabs.pl/targets/download-photometry/
```
### Using Python Script

You can use a Python script to create a new target:

```bash
python download_photometry.py <yourToken> <targetName>
```

## 2. Radio data download

With this API one can download all radio observations (mJy) in semi-color separated form. The columns of the output are the following: 

***MJD;mJy;Error;Facility;Filter;Observer***
### Request 
- **Method**: POST
- **URL**: `/targets/download-radio/`

### Request Parameters

- `name` (string, required): The name or identifier of the target.

### Example Request Body

```json
{
    "name": "My Target",
}
```

### Example Request

You can make a POST request to download the data using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "name": "My Target",
  }' \
  https://bh-tom2.astrolabs.pl/targets/download-radio/
```
### Using Python Script

You can use a Python script to create a new target:

```bash
python download_radio.py <yourToken> <targetName>
```


# TARGETS API

## 1. Create Target 
<!-- /targets/createTarget/ -->

  This API allows users to create targets.

### Request

- **Method**: POST
- **URL**: `/targets/createTarget/`

### Request Parameters

The request to create a new Sidereal target should include the following parameters in the request body:

- `name` (string, required): The name or identifier of the target.
- `ra` (number, required): The Right Ascension (RA) of the target, represented as a floating-point number.
- `dec` (number, required): The Declination (Dec) of the target, represented as a floating-point number.
- `epoch` (number): The epoch or reference time for the target (e.g., 2000.0).
<!-- - `type` (string): SIDEREAL or NONSIDEREAL type of object, default: SIDEREAL -->
- `classification` (string): The classification or type of the target.
- `discovery_date` (string, datetime format): The date and time of the target's discovery.
- `importance` (number): A numerical value representing the importance or priority of the target.
- `description` (stringr): Your description to target.
- `cadence` (number): A numerical value representing the cadence or frequency of observations for the target.

### Example Request Body

```json
{
    "name": "My Target",
    "ra": 123.456,
    "dec": -45.678,
    "epoch": 2000.0,
    "classification": "Star",
    "discovery_date": "2023-09-28T10:00:00Z",
    "importance": 5,
    "cadence": 24,
    "description": "TEST"
}
```

### Example Request

You can make a POST request to create a new target using the `curl` command or a Python script. 

### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "name": "My Target",
    "ra": 123.456,
    "dec": -45.678,
    "epoch": 2000.0,
    "classification": "Star",
    "discovery_date": "2023-09-28T10:00:00Z",
    "importance": 5,
    "cadence": 24
  }' \
  https://bh-tom2.astrolabs.pl/targets/createTarget/
```
### Using Python Script

You can use a Python script to create a new target:

```bash
python create_target.py --name "My Target" --ra 123.456 --dec -45.678 --epoch 2000.0 --classification "Star" --discovery_date "2023-09-28T10:00:00Z" --importance 5 --cadence 24 --token <yourToken> 
```

List of available classifications:

```("Unknown", "Unknown"), 
    ('Be-star outburst', 'Be-star outburst'),
    ('AGN', "Active Galactic Nucleus(AGN)"), 
    ("BL Lac", "BL Lac"),
    ("CV", "Cataclysmic Variable(CV)"), 
    ("CEPH", "Cepheid Variable(CEPH)"),
    ("EB", "Eclipsing Binary(EB)"),
    ("Galaxy", "Galaxy"), 
    ("LPV", "Long Period Variable(LPV)"),
    ("LBV", "Luminous Blue Variable(LBV)"),
    ("M-dwarf flare", "M-dwarf flare"), 
    ("Microlensing Event", "Microlensing Event"), 
    ("Nova", "Nova"),
    ("Peculiar Supernova", "Peculiar Supernova"),
    ("QSO", "Quasar(QSO)"), 
    ("RCrB", "R CrB Variable"), 
    ("RR Lyrae Variable", "RR Lyrae Variable"),
    ("SSO", "Solar System Object(SSO)"),
    ("Star", "Star"), 
    ("SN", "Supernova(SN)"), 
    ("Supernova imposter", "Supernova imposter"),
    ("Symbiotic star", "Symbiotic star"),
    ("TDE", "Tidal Disruption Event(TDE)"), 
    ("Variable star-other", "Variable star-other"),
    ("XRB", "X-Ray Binary(XRB)"),
    ("YSO", "Young Stellar Object(YSO)")
```

## 2. Update Target
<!-- /targets/updateTarget/{name}/ -->

This API allows users to update an existing target with new information.

### Request

- **Method**: PATCH
- **URL**: `/targets/updateTarget/{name}/`

Here, `{name}` is the name or identifier of the target you want to update.


### Request Parameters

The request to update a target should include the following parameters in the request body:

- `name` (string): The name or identifier of the target. This parameter is part of the URL and does not need to be included in the request body.
- `ra` (number, optional): The Right Ascension (RA) of the target, represented as a floating-point number.
- `dec` (number, optional): The Declination (Dec) of the target, represented as a floating-point number.
- `epoch` (string, optional): The epoch or reference time for the target (e.g., 2000.0).
- `classification` (string, optional): The classification or type of the target.
- `discovery_date` (string, datetime format, optional): The date and time of the target's discovery.
- `importance` (number, optional): A numerical value representing the importance or priority of the target.
- `cadence` (number, optional): A numerical value representing the cadence or frequency of observations for the target.

### Example Request Body

```json
{
    "ra": 135.789,
    "dec": -30.123,
    "epoch": "J2023",
    "classification": "Galaxy",
    "discovery_date": "2022-12-15T08:30:00Z",
    "importance": 3,
    "cadence": 12
}
```

### Example Request

You can make a PATCH request to update an existing target using the `curl` command or a Python script.

### Using `curl`

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "ra": 135.789,
    "dec": -30.123,
    "epoch": "J2023",
    "classification": "Galaxy",
    "discovery_date": "2022-12-15T08:30:00Z",
    "importance": 3,
    "cadence": 12
  }' \
  https://bh-tom2.astrolabs.pl/targets/updateTarget/{name}/
```

Replace `<yourToken>` with your authentication token and `{name}` with the actual name or identifier of the target you want to update.
Note, the last slash is required!

### Using Python Script

You can use a Python script to update an existing target with Token Authentication:

```bash
  python update_target.py "My Target" --ra 135.789 --dec -30.123 --epoch "J2023" --classification "Galaxy" --discovery_date "2022-12-15T08:30:00Z" --importance 3 --cadence 12 --token <yourToken> 
```

## 3. Target List
<!-- targets/getTargetList/ -->

This API allows users to obtain a list of targets. 
This API supports filtering targets by name, Right Ascension (RA) range, and Declination (Dec) range.
You can requested only 200 records per request, use pramater "page" to get more records 

### Request

- **Method**: POST
- **URL**: `/targets/getTargetList/`

### Request Parameters

The request to retrieve the target list may include the following query parameters:

- `name` (string): The name or identifier of the target.
- `type` (string, optional): Type of the target.
- `raMin` (number, optional): The minimum Right Ascension (RA) value.
- `raMax` (number, optional): The maximum Right Ascension (RA) value.
- `decMin` (number, optional): The minimum Declination (Dec) value.
- `decMax` (number, optional): The maximum Declination (Dec) value.
- `importanceMin` (number, optional): The minimum importance value.
- `importanceMax` (number, optional): The maximum importance value.
- `classification` (string, optional): Classification of the target.
- `targetGroup` (string, optional): Name of the target group.
- `coneSearchTarget` (string, optional): Target name and search radius, format: `"TargetName,Radius"`.
- `coneSearchRaDecRadius` (string, optional): RA, Dec and search radius, format: `"RA,Dec,Radius"`.
- `priority` (number, optional): Observing priority.
- `galacticLatMin` (number, optional): Minimum galactic latitude.
- `galacticLatMax` (number, optional): Maximum galactic latitude.
- `galacticLonMin` (number, optional): Minimum galactic longitude.
- `galacticLonMax` (number, optional): Maximum galactic longitude.
- `description` (string, optional): Description of the target.
- `sunSeparationMin` (number, optional): Minimum sun separation.
- `sunSeparationMax` (number, optional): Maximum sun separation.
- `lastMagMin` (number, optional): Minimum last magnitude.
- `lastMagMax` (number, optional): Maximum last magnitude.
- `page` (number, optional): The number of requested page.

### Example Request

You can make a POST request to retrieve a list of targets based on the specified criteria using the `curl` command or a web browser.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyTarget",
    "raMin": 100.0,
    "raMax": 200.0,
    "decMin": -30.0,
    "decMax": 30.0,
    "importanceMin": 1,
    "importanceMax": 10,
    "classification": "Star",
    "targetGroup": "GroupA",
    "coneSearchTarget": "TA,0.4",
    "coneSearchRaDecRadius": "3.11,2.11,0.4",
    "priority": 5,
    "galacticLatMin": -10,
    "galacticLatMax": 10,
    "galacticLonMin": 100,
    "galacticLonMax": 200,
    "description": "Test target",
    "sunSeparationMin": 30,
    "sunSeparationMax": 90,
    "lastMagMin": 15,
    "lastMagMax": 20,
    "page": 1
  }' \
  "https://bh-tom2.astrolabs.pl/targets/getTargetList/"
```

Replace `<yourToken>` with your authentication token and adjust the URL as needed to specify your search criteria.


## 4. Delete Target
<!-- targets/deleteTarget/ -->

This API supports deleting a target by providing its name.

### Request

The endpoint for retrieving a list of targets based on criteria is:


- **Method**: DELETE
- **URL**: `/targets/deleteTarget/`


### Request Parameters

The request to delete a target should include the following parameters in the request body:

- `name` (string, required): The name or identifier of the target that you want to delete.

### Example Request Body

```json
{
    "name": "MyTarget"
}
```

### Example Request

You can make a DELETE request to delete a target using the `curl` command or a web browser.

### Using `curl`

```bash
curl -X DELETE \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "name": "MyTarget"
  }' \
  https://bh-tom2.astrolabs.pl/targets/deleteTarget/
```

Replace `<yourToken>` with your authentication token and `"MyTarget"` with the name or identifier of the target you want to delete.

## 5. Targets: get plots

<!-- targets/get-plots/ -->
This API allows users to obtain the plots for a list of targets. The plots are returned in JSON format and in order to be displayed, one has to use plotly or matplotlib libraries.

### Request
- **Method**: POST
- **URL**: `targets/get-plots/`

### Request Parameters

The request to retrieve plots should include the following parameters in the request body:

- `targetNames` (array of strings, required): An array of target names or identifiers for which you want to retrieve plots.

### Example Request Body

```json
{
    "targetNames": ["Target1", "Target2", "Target3"]
}
```

### Request Headers

To authorize the request, you should include Token Authentication by providing a valid authentication token in the request headers.

- `Authorization: Token <yourToken>`: Authentication token for the API.

### Example Request Headers

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
    "targetNames": ["Target1", "Target2", "Target3"]
  }' \
https://bh-tom2.astrolabs.pl/targets/get-plots/
```

Replace `<yourToken>` with your valid authentication token and adjust the target names in the request body as needed.

## 6. Clean Target list cache (ADMINs only)
<!-- /targets/cleanTargetListCache/ -->

This document provides information about the Clean Target List Cache API, which allows authorized users to clear the cache for the target list. Caching is used to improve the performance of retrieving target lists, and this API provides a way to manually refresh the cached data.

### Request

The endpoint for retrieving a list of targets based on criteria is:

- **Method**: POST
- **URL**: `/targets/cleanTargetListCache/`

To clear the target list cache, you should make a POST request to the above endpoint with the following requirements:

- Token Authentication: You must include a valid authentication token in the request headers.
- User Authorization: Only users with superuser privileges are authorized to clean the cache.

### Example Request

You can make a POST request to clean the target list cache using the `curl` command or any HTTP client that supports POST requests.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  "https://bh-tom2.astrolabs.pl/targets/cleanTargetListCache/"
```

Replace `<yourToken>` with your valid authentication token.


## 7. Clean Target Details Cache (ADMINs only)
<!-- targets/cleanTargetDetailsCache/ -->

This document provides information about the Clean Target Details Cache API, which allows authorized users to clear the cache for target details. Caching is used to improve the performance of retrieving target details, and this API provides a way to manually refresh the cached data.

### Request
- **Method**: POST
- **URL**: `targets/cleanTargetDetailsCache/`

To clear the target details cache, you should make a POST request to the above endpoint with the following requirements:

- Token Authentication: You must include a valid authentication token in the request headers.
- User Authorization: Only users with superuser privileges are authorized to clean the cache.

### Example Request

You can make a POST request to clean the target details cache using the `curl` command or any HTTP client that supports POST requests.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  "https://bh-tom2.astrolabs.pl/targets/cleanTargetDetailsCache/"
```

Replace `<yourToken>` with your valid authentication token.


## 8 Downloaded Target List (ADMIN ONLY)
<!-- targets/get-downloaded-target-list/ -->

This API allows admin users to obtain a list of downloaded targets. 
This API supports filtering downloaded targets by target name, username, creation date range, and download type.
You can request only 200 records per request; use the parameter "page" to get more records.

### Request

- **Method**: POST
- **URL**: `/targets/get-downloaded-target-list/`

### Request Parameters

The request to retrieve the downloaded target list may include the following query parameters:

- `target` (string, optional): The name or identifier of the target.
- `user` (string, optional): The username of the user who downloaded the target.
- `created_from` (string, optional): The start date-time (ISO format) for filtering downloads based on creation date.
- `created_to` (string, optional): The end date-time (ISO format) for filtering downloads based on creation date.
- `download_type` (string, optional): The type of download.
- `page` (number, optional): The number of the requested page.

### Example Request

You can make a POST request to retrieve a list of downloaded targets based on the specified criteria using the `curl` command or a web browser.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
        "target": "MyTarget",
        "user": "admin",
        "created_from": "2023-01-01T00:00:00Z",
        "created_to": "2024-01-01T00:00:00Z",
        "download_type": "R",
        "page": 1
      }' \
  "https://bh-tom2.astrolabs.pl/targets/getDownloadedTargetList/"

```

## 9 Get Target Groups 
<!-- targets/target-groups/ -->

This API allows *users to retrieve a paginated list of target groups. 
You can request a specific page of target groups by passing the `page` parameter

### Request

- **Method**: POST
- **URL**: `/targets/target-groups/`

### Request Parameters

The request to retrieve the target groups may include the following query parameters:

- `page` (integer, optional): The page number for pagination. Defaults to `1` if not provided.

### Headers

- `Authorization` (string, required): The token for authenticating the user. Format: `Token <yourToken>`.

### Example Request

You can make a POST request to retrieve a list of target groups using the `curl` command or an API client like Postman.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
        "page": 1
      }' \
  "https://bh-tom2.astrolabs.pl/targets/target-groups/"
  ```

## 10 Get Targets From Group 
<!-- targets/targets-from-group/ -->

This API allows users to retrieve a paginated list of targets associated with a specific target group. You can specify the target group either by its `id` or `name`, but not both.

### Request

- **Method**: POST
- **URL**: `/targets/targets-from-group/`

### Request Parameters

The request to retrieve the targets from a specific group may include the following parameters:
- `page` (integer, optional): The page number for pagination. Defaults to `1` if not provided.
- `id` (integer, optional): The ID of the target group. You must provide either `id` or `name`.
- `name` (string, optional): The name of the target group. You must provide either `id` or `name`.

### Headers

- `Authorization` (string, required): The token for authenticating the user. Format: `Token <yourToken>`.

### Example Request

You can make a POST request to retrieve a list of targets from a specific group using the `curl` command or an API client like Postman.

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  -H "Content-Type: application/json" \
  -d '{
        "id": 1,
        "page": 1
      }' \
  "https://bh-tom2.astrolabs.pl/targets/targets-from-group/"
```

## 11. GetCommentsApi
<!-- /common/api/comments/ -->

This API endpoint allows users to filter comments based on various parameters, such as target name, target ID, username, comment text, and creation date range. Pagination is available to retrieve results in manageable sets.

<!-- TOKEN is required! -->

### Request

- **Method**: `POST`
- **URL**: `/common/api/comments/`

### Parameters

- `target` (string): The name of the target to filter comments for.
- `targetid` (integer): The ID of the target to filter comments for.
- `user` (string): The username of the user who made the comment.
- `text` (string): A string to search within the comment text.
- `created_start` (string): The start date for filtering comments (format: `YYYY-MM-DD`).
- `created_end` (string): The end date for filtering comments (format: `YYYY-MM-DD`).
- `page` (integer): The number of the requested page for pagination (default is 1).

### Example Request Body (Optional)

```json
{
  "target": "ExampleTarget",
  "targetid": 123,
  "user": "example_user",
  "text": "search text",
  "created_start": "2024-01-01",
  "created_end": "2024-10-01",
  "page": 1
}
```
### Using `curl`

```bash
curl -X 'POST' \
  "https://bh-tom2.astrolabs.pl/common/api/comments/" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token <yourToken>' \
  -d '{ 
  "target": "ExampleTarget",
  "targetid": 123,
  "user": "example_user",
  "text": "search text",
  "created_start": "2024-01-01",
  "created_end": "2024-10-01",
  "page": 1
}'
```


# DATAPRODUCT API

### List Data Products

API for DataProduct list, which lists uploaded instrumental or fits files and tracks the user who uploaded them.

---

### Request

- **Method**: POST
- **URL**: `common/api/data/`

- Token Authentication: You must include a valid authentication token in the request headers.

#### Parameters

| Parameter          | Type     | Description                                                                 |
|--------------------|----------|-----------------------------------------------------------------------------|
| id                 | Integer  | Unique identifier for the data product.                                    |
| data_product_type  | String   | Type of data product (e.g., photometry, spectroscopy).                      |
| status             | String   | Status of the data product.                                                |
| fits_data          | String   | Name of the fits file.                                                     |
| photometry_data    | String   | Name of the photometry file.                                               |
| oname              | String   | Name of the observatory (replaces "camera").                               |
| created_start      | String   | Start date for creation date filter (ISO 8601 format).                     |
| created_end        | String   | End date for creation date filter (ISO 8601 format).                       |
| mjd                | String   | Modified Julian Date.                                                      |
| target_name        | String   | Name of the target.                                                        |
| target_id          | Integer  | Identifier of the target.                                                  |
| mag_min            | Float    | Minimum value of magnitude (inclusive).                                    |
| mag_max            | Float    | Maximum value of magnitude (inclusive).                                    |
| magerr_min         | Float    | Minimum value of magnitude error (inclusive).                              |
| magerr_max         | Float    | Maximum value of magnitude error (inclusive).                              |
| filter             | String   | Filter of the data product (e.g., "GaiaSP/U").                            |
| mjd_min            | Float    | Minimum value of Modified Julian Date (inclusive).                         |
| mjd_max            | Float    | Maximum value of Modified Julian Date (inclusive).                         |
| page               | Integer  | Page number for pagination (default: 1).                                   |

---

### Example Request Body

```json
{
    "data_product_type": "photometry",
    "id": 1,
    "status": "Dataproduct status",
    "fits_data": "fits file name",
    "photometry_data": "photometry file name",
    "oname": "BIALKOW_ANDOR-DW432",
    "created_start": "2024-01-01",
    "created_end": "2024-01-02",
    "mjd": "2",
    "target_name": "Star123",
    "target_id": 42,
    "mag_min": 15.0,
    "mag_max": 20.0,
    "magerr_min": 0.01,
    "magerr_max": 0.1,
    "filter": "GaiaSP/U",
    "mjd_min": 59000.0,
    "mjd_max": 59010.0,
    "page": 2
}
```

---

### Example Request

You can make a POST request using the `curl` command or any HTTP client that supports POST requests. Only 500 records can be requested per page; use the "page" parameter to retrieve subsequent records.

#### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  "https://bh-tom2.astrolabs.pl/common/api/data/"
```

Replace `<yourToken>` with your valid authentication token.

#### With Request Body

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Token <yourToken>" \
  "https://bh-tom2.astrolabs.pl/common/api/data/" \
  -d '{
    "data_product_type": "photometry",
    "id": 1,
    "status": "Dataproduct status",
    "fits_data": "fits file name",
    "photometry_data": "photometry file name",
    "oname": "BIALKOW_ANDOR-DW432",
    "created_start": "2024-01-01",
    "created_end": "2024-01-02",
    "mjd": "2",
    "target_name": "Star123",
    "target_id": 42,
    "mag_min": 15.0,
    "mag_max": 20.0,
    "magerr_min": 0.01,
    "magerr_max": 0.1,
    "filter": "GaiaSP/U",
    "mjd_min": 59000.0,
    "mjd_max": 59010.0,
    "page": 2
  }'
```
Ensure that your authentication token is valid and your parameters are correctly specified to get the desired results.


### Delete Data Product

This API allows you to delete a specific data product by its ID.

### Request
- **Method**: DELETE
- **URL**: `common/api/deleteDataProduct/`

- **Token Authentication**: You must include a valid authentication token in the request headers.
- **Admin Access Required**: Only users with admin privileges can access this API.

### Required Body Parameters
- `id` (string): The ID of the data product to be deleted.

### Example Request

You can make a POST request using the `curl` command or any HTTP client.

#### Using `curl`

```bash
curl -X DELETE \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "id": "12345"
  }' \
  "https://bh-tom2.astrolabs.pl/common/api/deleteDataProduct/"
```

Replace `<yourToken>` with your valid authentication token and `12345` with the ID of the data product you want to delete.



# Reduced Datum API

### List Reduced Datums
### Request
- **Method**: POST
- **URL**: `common/api/reducedDatum/`

- Token Authentication: You must include a valid authentication token in the request headers.


### Example Request Body

please provide target_name or target_id, not both of them
```json
{
    "target_name": "MyTarget",
    "target_id": 1,
    "page": "1",
}
```
### Example Request

You can make a POST request using the `curl` command or any HTTP client that supports POST requests. You can request only 500 records for one request, use parametr "page" to get next 500 records

### Using `curl`

```bash
curl -X POST \
  -H "Authorization: Token <yourToken>" \
  "https://bh-tom2.astrolabs.pl/common/api/reducedDatum/"
```

Replace `<yourToken>` with your valid authentication token.


```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Token <yourToken>" \
  "https://bh-tom2.astrolabs.pl/common/api/reducedDatum/"  -d '{ 
  "target_name": "ExampleTarget",
  "page": 1
}' 
```

### Delete Reduced Datum

This API allows you to delete a specific reduced datum (measurement) with an optional flag to delete associated data products.

### Request
- **Method**: DELETE
- **URL**: `common/api/deleteReducedDatum/`

- **Token Authentication**: You must include a valid authentication token in the request headers.
- **Admin Access Required**: Only users with admin privileges can access this API.

### Required Query Parameters
- `mjd` (float): Modified Julian Date (precision up to 1e-6).
- `mag` (float): Magnitude (precision up to 1e-3).
- `magerr` (float): Magnitude error (precision up to 1e-3).
- `filter` (string): Filter used (e.g., V, R, I).
- `observer` (string): Observer name.

### Optional Query Parameters
- `target_name` (string): Name of the target (provide either `target_name` or `target_id`, not both).
- `target_id` (integer): ID of the target (provide either `target_name` or `target_id`, not both).
- `delete_associated_data_product` (boolean): Whether to delete the associated data product (default: `False`).

### Example Request

You can make a DELETE request using the `curl` command or any HTTP client.

#### Using `curl`

```bash
curl -X DELETE \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "target_name": "MyTarget",
    "mjd": 59580.123456,
    "mag": 15.123,
    "magerr": 0.001,
    "filter": "V",
    "observer": "ObserverName",
    "delete_associated_data_product": true
  }' \
  "https://bh-tom2.astrolabs.pl/common/api/deleteReducedDatum/"
```

Replace `<yourToken>` with your valid authentication token.

Here's the documentation for the `DeactivateReducedDatumApiView` in the style of the `DeleteReducedDatum` documentation:

---

### Deactivate Reduced Datum

This API allows you to deactivate a specific reduced datum (measurement) with an optional flag to deactivate associated data products.

### Request
- **Method**: POST
- **URL**: `common/api/deactivateReducedDatum/`

- **Token Authentication**: You must include a valid authentication token in the request headers.
- **Admin Access Required**: Only users with admin privileges can access this API.

### Required Body Parameters
- `mjd` (float): Modified Julian Date (precision up to 1e-6).
- `mag` (float): Magnitude (precision up to 1e-3).
- `magerr` (float): Magnitude error (precision up to 1e-3).
- `filter` (string): Filter used (e.g., V, R, I).
- `observer` (string): Observer name.

### Optional Body Parameters
- `target_name` (string): Name of the target (provide either `target_name` or `target_id`, not both).
- `target_id` (integer): ID of the target (provide either `target_name` or `target_id`, not both).

### Example Request

You can make a POST request using the `curl` command or any HTTP client.

#### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "target_name": "MyTarget",
    "mjd": 59580.123456,
    "mag": 15.123,
    "magerr": 0.001,
    "filter": "V",
    "observer": "ObserverName"
  }' \
  "https://bh-tom2.astrolabs.pl/common/api/deactivateReducedDatum/"
```

Replace `<yourToken>` with your valid authentication token.


# Calibration Data ADMIN API


### Restart Calibration By CALIB ID 

This API allows you to restart the calibration by id  process with various optional filters.

### Request
- **Method**: POST
- **URL**: `calibration/restart-calib-by-id/`

- **Token Authentication**: You must include a valid authentication token in the request headers.
- **Admin Access Required**: Only users with admin privileges can access this API.

### Optional Query Parameters

- `id_from` (integer): The starting ID for the range (optional).
- `id_to` (integer): The ending ID for the range (optional).
- `filter` (string): The new filter value to use for recalibration (optional).
- `old_filter` (string): The old filter value to query data for recalibration (optional).
- `match_dist` (float): The match distance filter to set for the new calibration (default is -1) (optional).
- `oname` (string): The observatory name to query data for recalibration (optional).
- `comment` (string): A comment or note for the recalibration process (optional).
- `status` (string): The calibration status to query data for recalibration (optional).
- `status_message` (string): The status message to query data for recalibration (optional).

### Example Request

You can make a POST request using the `curl` command or any HTTP client.

#### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "id_from": 100,
    "id_to": 200,
    "filter": 3,
    "old_filter": 2,
    "match_dist": 0,
    "oname": 1,
    "comment": "Restarting calibration",
    "status": 1,
    "status_message": "Calibration restarted"
  }' \
  "https://bh-tom2.astrolabs.pl/calibration/restart-calib-by-id/"
```

Replace `<yourToken>` with your valid authentication token.


### Restart Calibration by Target

This API allows you to restart the calibration process based on a target name/id and MJD range with various optional filters.

### Request
- **Method**: POST
- **URL**: `calibration/restart-calib-by-target/`

- **Token Authentication**: You must include a valid authentication token in the request headers.
- **Admin Access Required**: Only users with admin privileges can access this API.

### Optional Query Parameters
- `target_name` (string): The name of the target to query data for recalibration (optional).
- `target_id` (integer): The ID of the target to query data for recalibration (optional).
- `mjd_max` (float): The maximum Modified Julian Date (MJD) for the recalibration filter (optional).
- `mjd_min` (float): The minimum Modified Julian Date (MJD) for the recalibration filter (optional).
- `filter` (string): The new filter value to use for recalibration (optional).
- `old_filter` (string): The old filter value to query data for recalibration (optional).
- `match_dist` (float): The match distance filter to set for the new calibration (optional).
- `oname` (string): The observatory name to query data for recalibration (optional).
- `comment` (string): A comment or note for the recalibration process (optional).
- `status` (string): The calibration status to query data for recalibration (optional).
- `status_message` (string): The status message to query data for recalibration (optional).

### Example Request

You can make a POST request using the `curl` command or any HTTP client.

#### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "target_name": "MyTarget",
    "target_id": 123,
    "mjd_max": 59580,
    "mjd_min": 59579,
    "filter": 3,
    "old_filter": 2,
    "match_dist": 0,
    "oname": 1,
    "comment": "Restarting calibration for target",
    "status": 1,
    "status_message": "Calibration restarted successfully"
  }' \
   "https://bh-tom2.astrolabs.pl/calibration/restart-calib-by-target/"
```

Replace `<yourToken>` with your valid authentication token.



### Notes
- You must provide either `target_name` or `target_id` but not both.
- You must be an admin to access this endpoint.


### Restart Calibration by Data Product

This API allows you to restart the calibration process for a specific data product with optional parameters for quering and customization.

### Request
- **Method**: POST  
- **URL**: `calibration/restart-calib-by-dataproduct/`  
- **Token Authentication**: You must include a valid authentication token in the request headers.  
- **Admin Access Required**: Only users with admin privileges can access this API.

### Optional Query Parameters
- `data_product_id` (integer): The ID of the data product to restart calibration for.
- `filter` (string): The new filter value to apply for calibration (optional).
- `old_filter` (string): The old filter value to query data for recalibration (optional).
- `match_dist` (float): The match distance filter for the new calibration (optional).
- `oname` (string): The observatory name to query data for recalibration (optional).
- `comment` (string): A comment or note for the recalibration process (optional).
- `status` (string): The calibration status to query data for recalibration (optional).
- `status_message` (string): The status message to query data for recalibration (optional).

### Example Request

You can make a POST request using the `curl` command or any HTTP client.

#### Using `curl`

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <yourToken>" \
  -d '{
    "data_product_id": 123,
    "filter": 5,
    "old_filter": 3,
    "match_dist": 2,
    "oname": 10,
    "comment": "Restarting calibration with new parameters",
    "status": 1,
    "status_message": "Calibration initiated"
  }' \
   "https://bh-tom2.astrolabs.pl/calibration/restart-calib-by-dataproduct/"
```

Replace `<yourToken>` with your valid authentication token.



# GET USERS DETAILS API

### Description

This API allows admin users to retrieve a list of user accounts from the BHTOM system based on optional filters such as `id`, `username`, and `created` (registration date). You must be an **admin user** to access this endpoint.

### Endpoint

* **Method**: POST
* **URL**: `common/api/users/`
* **Authentication**: Token required
* **Permissions**: Must be admin (`is_staff = True`)

### Request Parameters (JSON Body)

| Parameter  | Type   | Required | Description                                       |
| ---------- | ------ | -------- | ------------------------------------------------- |
| `id`       | string | No       | Filter by User ID                                 |
| `username` | string | No       | Filter by Username                                |
| `created`  | string | No       | Filter users created after this date (YYYY-MM-DD) |

### Example Request

```bash
curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/common/api/users/' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "john",
    "created": "2023-01-01"
}'
```

### Successful Response (200 OK)

Returns a list of user objects:

```json
[
  {
    "id": 12,
    "username": "john",
    "email": "john@example.com",
    "date_joined": "2023-01-15T14:23:00Z",
    ...
  }
]
```

### Error Responses

* `403 Forbidden`: User is not an admin
* `500 Internal Server Error`: Unexpected server-side failure

---

# CHANGE OBSERVERS API

### Description

This API allows authenticated users to update the list of observers associated with a **Data Product** by specifying its ID and a list of usernames.

### Endpoint

* **Method**: POST
* **URL**: `common/api/changeObservers/`
* **Authentication**: Token required
* **Permissions**: Must be authenticated

### Request Parameters (JSON Body)

| Parameter   | Type   | Required | Description                           |
| ----------- | ------ | -------- | ------------------------------------- |
| `id`        | string | Yes      | ID of the DataProduct to update       |
| `observers` | array  | Yes      | List of usernames to set as observers |

### Example Request

```bash
curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/common/api/changeObservers/' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "123456",
    "observers": ["alice", "bob"]
}'
```

### Successful Response (200 OK)

Returns the updated DataProduct object:

### Error Responses

* `400 Bad Request`: Missing required fields or invalid data
* `404 Not Found`: DataProduct with the given ID does not exist
* `500 Internal Server Error`: Unexpected server error





# DOWNLOAD PHOTOMETRY FILE API

### Description

This API allows authenticated users to download a photometry file (.dat) by data product id.

### Endpoint

* **Method**: POST
* **URL**: `common/api/downloadPhotometryFile/`
* **Authentication**: Token required
* **Permissions**: Must be authenticated

### Request Parameters (JSON Body)

| Parameter   | Type   | Required | Description                           |
| ----------- | ------ | -------- | ------------------------------------- |
| `id`        | string | Yes      | ID of the DataProduct                 |

### Example Request

```bash
curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/common/api/downloadPhotometryFile/' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "123456",
}'
```

### Successful Response (200 OK)

Returns photometry file:

### Error Responses

* `400 Bad Request`: Missing required fields or invalid data
* `404 Not Found`: DataProduct with the given ID does not exist
* `500 Internal Server Error`: Unexpected server error


