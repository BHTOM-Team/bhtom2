
# BHTOM2 API Documentation

## Introduction

This is a simple guide for BHTOM's REST API. It lets you use BHTOM webpage features in your own programs. You can get a list of targets, add observations, download data and more. Let's get started!

> **Remember!** To use API you should get your own TOKEN first!

# 1. AUTHORIZATION API: /api/token-auth/

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


# 2. PHOTOMETRY UPLOAD API

### Description
This API facilitates programmable batch file uploads to the **BHTOM system**. It offers a command-line interface for uploading files along with their associated meta data.

<!-- Please note, an authentication `TOKEN` is required to use this script. -->

### Endpoint

- **Method**: POST
- **URL**: `/upload`

### Usage

The ready-to-use script is located in the `documentation_scripts` folder.

```bash
python upload_files_script.py  <token> <target> <data_product_type> <files> [--match_dist <match_dist>] [--comment <comment>] [--dry_run] [--no_plot] [--mjd <mjd>] [--group <group>] [--observer <observer>]
```

### Arguments

- `<token>`: Your authentication token
- `<target>`: Target destination for the uploaded files
- `<data_product_type>`: Type of data product: `fits_file`, `photometry` (instrumental in SExtractor format), `photometry_nondetection`, `spectroscopy`
- `<files>`: Comma-separated list of files to be uploaded
<!-- TODO: LW: check photometry vs SExtractor, we need both: WILL BE ADDED -->
### Optional Arguments

<!-- - `--match_dist <match_dist>`: This sets the matching distance (float) for astrometric cross-match in the standardisation procedure.  -->
<!-- LW: I hid the match_dist as we set it fixed -->
- `--comment <comment>`: comment to your upload
- `--dry_run`: if true, the script will be run in Dry Run (test) mode. The data will processed but will not be stored in the database. The default is false.
- `--no_plot`: if true, no calibration plot will be generated. The default setting is false.
- `--mjd <mjd>`: Modified Julian Date (float) [note MJD=JD-2400000.5]
<!-- - `--group <group>`: target group where to add -->
<!-- TODO: what groups are here? -->
- `--observer <observer>`: name of the observer


### Example Usage

```bash
python upload_files_script.py 123token456 Gaia22bpl photometry file1.cat,file2.cat --mjd 51234.123
```

### Advanced Usage

```bash
# python upload_files_script.py abc123 target2 type2 file3.txt --match_dist 0.5 --comment "Example comment" --dry_run --no_plot --mjd 59371.5 --group "example_group" --observer "John Doe"
python upload_files_script.py abc123 target2 type2 file3.txt --comment "my batch upload on 2023-10-02" --dry_run --no_plot --mjd 59371.5 --observer "John Doe"
```

### Response

The script will display the response from the API with a list of uploaded files with id of each file, so you can check the calibrations result by their ids.

### Dependencies

- Python 3.x
- The `requests` library (install with `pip install requests`)


# CALIBRATIONS API

### Description

<!-- This Python script allows you to retrieve a list of catalogues from the BHTOM2 system using the `get_catalogs` API. It provides a command-line interface for making GET requests with proper authorization. -->

<!-- TOKEN is required! -->
<!-- 
### Endpoint

- **Method**: GET
- **URL**: `/calibration/get-catalogs/`

## Usage

```bash
python get_catalogs_script.py <token>
```

### Arguments

<token>: Authentication token.

### Example Usage

python get_catalogs_script.py https://example.com/get_catalogs_api abc123

### Response

The script will make a GET request to the API and display the list of available catalogs, including their IDs, names.

### Dependencies

Python 3.x
The requests library (install with pip install requests)

Certainly! Here's the documentation for the `curl` command you provided in Markdown format:

--- -->


### Description
 <!-- /calibration/get-calibration-res/ -->

This API endpoint allows users to retrieve calibration results for previously uploaded observations.

<!-- TOKEN is required! -->

### Request

- **Method**: POST
- **URL**: `/calibration/get-calibration-res`

### Request Headers

- `accept: application/json`: Specify the desired response format as JSON.
- `Authorization: Token 10f21fe7308f06f7e23ccb7848da554c2271be49`: Authentication token for the API.
- `Content-Type: application/json`: Specify the format of the request payload as JSON.
- `X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr`: CSRF token for security.

### Request Body

- `fileId` (array): Array containing file IDs for calibration
- `getPlot` (boolean): Flag to indicate whether to retrieve the calibration plot

### Example Request

```bash
curl -X 'POST' \
  'url/calibration/get-calibration-res/' \
  -H 'accept: application/json' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
    "fileId": [1],
    "getPlot": true
  }'
```
    You can use script as well

```bash
    python get_calib_res.py "yourToken" 1 2 3 --get_plot
```
### Response

    Response is the list with calibration result and plot(if getPlot=True) for each file id 


# OBSERVATORY API

# 1. Observatory List
<!-- /observatory/getObservatoryList/ -->
    
    This API endpoint allows users to get the list of observatories registered in the system.

    <!-- TOKEN is requaired! -->

### Request

- **Method**: POST
- **URL**: `/observatory/getObservatoryList/`

### Parameters

- `name` (string): A parameter for specifying a name.
- `prefix` (string): A parameter for specifying a prefix.
- `lon` (number): Longitude value.
- `lat` (number): Latitude value.
- `active_flg` (boolean): A flag to indicate whether an item is active.
- `created_start` (string): A date and time parameter for specifying a start date.
- `created_end` (string): A date and time parameter for specifying an end date.

### Example Request Body (Optional)

```json
{
  "name": "Example Name",
  "prefix": "EX",
  "lon": 123.456,
  "lat": 45.678,
  "active_flg": true,
  "created_start": "2023-09-01T12:00:00Z",
  "created_end": "2023-09-30T23:59:59Z"
}
```

### Request Header

The request header should include the following:

- `Authorization: Token <token>` (required): Authentication token for the API.

### Example Request

```bash
curl -X 'POST' \
  'url/observatory/getObservatoryList/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token <yourToken>' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
  "name": "string",
  "prefix": "string",
  "lon": 0,
  "lat": 0,
  "active_flg": true,
  "created_start": "2023-09-28T14:00:09.440Z",
  "created_end": "2023-09-28T14:00:09.440Z"
}'
```

### Response
    List of registered observatories



# 2. Add Favourite Observatory
<!-- /observatory/addFavouriteObservatory/ -->

This API endpoint allows users to add observatory to their favourite list. Users must provide the observatory name, and can include an optional comment.

### Request

- **Method**: POST
- **URL**: `/api/create-observatory-matrix/`

### Request Headers

- `Authorization: Token <yourToken>` (required): Authentication token for the API.

### Request Body

- `observatory` (string, required): The name of the observatory.
- `comment` (string, optional): An optional comment.

### Example Request Body

```json
{
  "observatory": "Observatory Name",
  "comment": "This is an optional comment."
}
```


### Example Request

```bash
curl -X POST \
  'url/observatory/addFavouriteObservatory/' \
  -H 'Authorization: Token <yourToken>' \
  -H 'Content-Type: application/json' \
  -d '{
    "observatory": "Observatory Name",
    "comment": "This is an optional comment."
  }'
```

# 3. Create Observatory 
<!-- /createObservatory/ -->

    This API allows users to create an observatory. 

### Request

- **Method**: POST
- **URL**: `/observatory/create/`

### Request Parameters

The request to create an observatory should include the following parameters in the request body:

- `name` (string, required): The name of the observatory.
- `lon` (number, float, required): The longitude coordinate of the observatory.
- `lat` (number, float, required): The latitude coordinate of the observatory.
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
    "calibration_flg": true,
    "example_file": "observatory_example.txt",
    "comment": "This observatory is for calibration purposes."
  }' \
  https://api.example.com/observatory/create/
```

### Using Python Script

You can use a Python script to create observatories:
```bash
python create_observatory.py --name "My Observatory" --lon 45.12345 --lat -120.67890 --calibration_flg --example_file "observatory_example.txt" --comment "This observatory is for calibration purposes" --token <yourToken> 
```

# 4. Update Observatory 
<!-- /observatory/update/ -->

    This API allows users to update observatory information. 
### Request

- **Method**: POST
- **URL**: `/observatory/update/`

### Request Parameters

The request to update an observatory should include the following parameters in the request body:

- `name` (string, required): The name of the observatory.
- `lon` (number, float, optional): The new longitude coordinate of the observatory.
- `lat` (number, float, optional): The new latitude coordinate of the observatory.
- `calibration_flg` (boolean, optional): A flag indicating whether the observatory is for calibration purposes only.
- `example_file` (string, optional): A new example file associated with the observatory.
- `comment` (string, optional): New additional comments or notes about the observatory.
- `altitude` (number, float, optional): The new altitude of the observatory.
- `gain` (number, float, optional): The new gain setting of the observatory's equipment.
- `readout_noise` (number, float, optional): The new readout noise of the observatory's equipment.
- `binning` (number, float, optional): The new binning factor used in observations.
- `saturation_level` (number, float, optional): The new saturation level of the equipment.
- `pixel_scale` (number, float, optional): The new pixel scale of the observatory's equipment.
- `readout_speed` (number, float, optional): The new readout speed of the equipment.
- `pixel_size` (number, float, optional): The new pixel size of the equipment.
- `approx_lim_mag` (number, float, optional): The new approximate limiting magnitude of the observatory.
- `filters` (string, optional): The new filters used in observations.

### Example Request Body

```json
{
    "name": "My Observatory",
    "lon": 45.12345,
    "lat": -120.67890,
    "calibration_flg": true,
    "example_file": "new_observatory_example.txt",
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
    "example_file": "new_observatory_example.txt",
    "comment": "Updated observatory information."
  }' \
  https://api.example.com/api/observatory/update/
```

### Using Python Script

You can use a Python script to update observatory information:

```bash
python create_observatory.py --name "My Observatory" --lon 45.12345 --lat -120.67890 --calibration_flg --example_file "observatory_example.txt" --comment "This observatory is for calibration purposes" --token <yourToken> 
```

# 5. Get Favourite Observatory
<!-- /observatory/getFavouriteObservatory/ -->

    This API allows obtaining a favourite observatory.

## Request

- **Method**: POST
- **URL**: `/observatory/getFavouriteObservatory/`

## Request Parameters

The request to retrieve observatory matrix data can include the following parameters in the request body:

- `user` (string, optional): Filter observatory matrix data by the username of the user associated with the observatory.
- `active_flg` (boolean, optional): Filter observatory matrix data by the active flag, indicating whether the observatory is active.
- `observatory` (string, optional): Filter observatory matrix data by the observatory name or identifier.
- `created_start` (string, datetime format, optional): Filter observatory matrix data to include only records created on or after the specified date and time.
- `created_end` (string, datetime format, optional): Filter observatory matrix data to include only records created on or before the specified date and time.

### Example Request Body

```json
{
    "user": "JohnDoe",
    "active_flg": true,
    "observatory": "My Observatory",
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
    "observatory": "My Observatory",
    "created_start": "2023-01-01T00:00:00Z",
    "created_end": "2023-12-31T23:59:59Z"
  }' \
  https://api.example.com/api/observatory-matrix/get-matrix/
```

### Using Python Script

You can use a Python script to retrieve observatory matrix data:

```bash
python get_observatory_matrix.py --user "JohnDoe" --active_flg true --observatory "My Observatory" --created_start "2023-01-01T00:00:00Z" --created_end "2023-12-31T23:59:59Z" --token <yourToken>
```

# 6. Delete Favourite Observatory
<!-- /observatory/deleteFavouriteObservatory/ -->

    This API allows users to delete favourite observatory records based on the observatory name from their list.
### Request

- **Method**: DELETE
- **URL**: `/observatory/deleteFavouriteObservatory/`


### Request Parameters

The request to delete an observatory matrix record should include the following parameter in the request body:

- `observatory` (string, required): The name or identifier of the observatory for which you want to delete the matrix record.

### Example Request Body

```json
{
    "observatory": "My Observatory"
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
    "observatory": "My Observatory"
  }' \
  https://api.example.com/api/observatory-matrix/delete/
```

### Using Python Script

You can use a Python script to delete an observatory matrix record:
```bash
python delete_observatory_matrix.py --observatory "My Observatory" --token <yourToken>"
```


# Targets API

### 1. Create Target 
<!-- /targets/createTarget/ -->

  This API allows users to create targets.

### Request

- **Method**: POST
- **URL**: `/targets/createTarget/`

### Request Parameters

The request to create a new target should include the following parameters in the request body:

- `name` (string, required): The name or identifier of the target.
- `ra` (number, required): The Right Ascension (RA) of the target, represented as a floating-point number.
- `dec` (number, required): The Declination (Dec) of the target, represented as a floating-point number.
- `epoch` (string): The epoch or reference time for the target (e.g., "J2000").
- `classification` (string): The classification or type of the target.
- `discovery_date` (string, datetime format): The date and time of the target's discovery.
- `importance` (number): A numerical value representing the importance or priority of the target.
- `cadence` (number): A numerical value representing the cadence or frequency of observations for the target.

### Example Request Body

```json
{
    "name": "My Target",
    "ra": 123.456,
    "dec": -45.678,
    "epoch": "J2000",
    "classification": "Asteroid",
    "discovery_date": "2023-09-28T10:00:00Z",
    "importance": 5,
    "cadence": 24
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
    "epoch": "J2000",
    "classification": "Asteroid",
    "discovery_date": "2023-09-28T10:00:00Z",
    "importance": 5,
    "cadence": 24
  }' \
  url/targets/createTarget/
```
### Using Python Script

You can use a Python script to create a new target:

```bash
python create_target.py --name "My Target" --ra 123.456 --dec -45.678 --epoch "J2000" --classification "Asteroid" --discovery_date "2023-09-28T10:00:00Z" --importance 5 --cadence 24 --token <yourToken> 
```


# 2. Update Target
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
- `epoch` (string, optional): The epoch or reference time for the target (e.g., "J2000").
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
  url/api/targets/updateTarget/{name}/
```

Replace `<yourToken>` with your authentication token and `{name}` with the actual name or identifier of the target you want to update.

### Using Python Script

You can use a Python script to update an existing target with Token Authentication:

```bash
  python update_target.py "My Target" --ra 135.789 --dec -30.123 --epoch "J2023" --classification "Galaxy" --discovery_date "2022-12-15T08:30:00Z" --importance 3 --cadence 12 --token <yourToken> 
```

# 3. Target List
<!-- targets/getTargetList/ -->

This API allows users to obtain a list of targets. 
This API supports filtering targets by name, Right Ascension (RA) range, and Declination (Dec) range.

### Request

- **Method**: GET
- **URL**: `/targets/getTargetList/`

### Request Parameters

The request to retrieve the target list may include the following query parameters:

- `name` (string): The name or identifier of the target.
- `raMin` (number, optional): The minimum Right Ascension (RA) value, represented as a floating-point number.
- `raMax` (number, optional): The maximum Right Ascension (RA) value, represented as a floating-point number.
- `decMin` (number, optional): The minimum Declination (Dec) value, represented as a floating-point number.
- `decMax` (number, optional): The maximum Declination (Dec) value, represented as a floating-point number.
<!-- TODO: need more fields!! -->
### Example Request

You can make a GET request to retrieve a list of targets based on the specified criteria using the `curl` command or a web browser.

### Using `curl`

```bash
curl -X GET \
  -H "Authorization: Token <yourToken>" \
  "url/targets/getTargetList/?name=MyTarget&raMin=100.0&raMax=200.0&decMin=-30.0&decMax=30.0"
```

Replace `<yourToken>` with your authentication token and adjust the URL as needed to specify your search criteria.


# 4. Delete Target
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
  url/targets/deleteTarget/
```

Replace `<yourToken>` with your authentication token and `"MyTarget"` with the name or identifier of the target you want to delete.

# 5. Targets: get plots

<!-- targets/get-plots/ -->
This API allows users to obtain the visual list of targets. Filtering criteria can be provided.

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
url/targets/get-plots/
```

Replace `<yourToken>` with your valid authentication token and adjust the target names in the request body as needed.

# 6. Clean Target list cache (ADMINs only)
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
  "url/targets/cleanTargetListCache/"
```

Replace `<yourToken>` with your valid authentication token.


# 7. Clean Target Details Cache (ADMINs only)
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
  "url/targets/cleanTargetDetailsCache/"
```

Replace `<yourToken>` with your valid authentication token.
