
# BHTOM2 Script Documentation

## Introduction

This scripts allows you to use the BHTOM2 by REST API.

To use API you shoud get your own TOKEN!

# AUTHORIZATION API 

# 1. /api/token-auth/

### Description

The `token-auth` API allows users to obtain an authentication token by providing their username and password.
With this token you can use all others API 

### Endpoint

- **Method**: POST
- **URL**: `/api/token-auth/`

### Request Parameters

- `username` (string, required): User's username for authentication.
- `password` (string, required): User's password for authentication.

### Example Request

```http
curl -X 'POST' \
  'http://127.0.0.1:8000/api/token-auth/' \
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


# PHOTOMETRY UPLOAD API

# 1. UPLOAD FILES

This script allows you to upload multiple files to the BHTOM2 system using the `/upload` API. It provides a command-line interface for uploading files with associated metadata.

The script is located in documentation_scripts folder
TOKEN is requaired!

### Endpoint

- **Method**: POST
- **URL**: `/upload`

## Usage

```bash
python upload_files_script.py  <token> <target> <data_product_type> <files> [--match_dist <match_dist>] [--comment <comment>] [--dry_run] [--no_plot] [--mjd <mjd>] [--group <group>] [--observer <observer>]
```

### Arguments

- `<token>`: Authentication token.
- `<target>`: Target of the uploaded files.
- `<data_product_type>`: Type of data product.
- `<files>`: Comma-separated list of files to upload.

### Optional Arguments

- `--match_dist <match_dist>`: Matching distance (float).
- `--comment <comment>`: Additional comment.
- `--dry_run`: Enable dry run mode (default is false).
- `--no_plot`: Disable plot generation (default is false).
- `--mjd <mjd>`: Modified Julian Date (float).
- `--observer <observer>`: Observer's name.

## Example Usage

### Basic Usage

```bash
python upload_files_script.py abc123 target1 type1 file1.txt,file2.jpg
```

### Advanced Usage

```bash
python upload_files_script.py abc123 target2 type2 file3.txt --match_dist 0.5 --comment "Example comment" --dry_run --no_plot --mjd 2459371.5 --group "example_group" --observer "John Doe"
```

## Response

The script will display the response from the API, In response you will get list of uploaded files with id of each file, so you can later get calibrations result by ids.

## Dependencies

- Python 3.x
- The `requests` library (install with `pip install requests`)




# CALIBRATIONS API

# 1. /calibration/get-catalogs/

This Python script allows you to retrieve a list of catalogs from the BHTOM2 system using the `get_catalogs` API. It provides a command-line interface for making GET requests with proper authorization.

TOKEN is requaired!

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

---


# 2. /calibration/get-calibration-res/

This API endpoint allows users to retrieve calibration results.
TOKEN is requaired!

## Request

- **Method**: POST
- **URL**: `/calibration/get-calibration-res`

### Request Headers

- `accept: application/json`: Specify the desired response format as JSON.
- `Authorization: Token 10f21fe7308f06f7e23ccb7848da554c2271be49`: Authentication token for the API.
- `Content-Type: application/json`: Specify the format of the request payload as JSON.
- `X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr`: CSRF token for security.

### Request Body

- `fileId` (array): Array containing file IDs for calibration.
- `getPlot` (boolean): Flag to indicate whether to retrieve the calibration plot.

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
## Response

    Response is the list with calibration result and plot(if getPlot=True) for each file id 



# OBSERVATORY API

# 1. /observatory/getObservatoryList/
    
    This API endpoint allows users get observaatory list, all parametrs are optional.
    TOKEN is requaired!

## Request
TOKEN is requaired!
- **Method**: POST
- **URL**: `/observatory/getObservatoryList/`

## Request Body (Optional)

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

## Request Header

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

## Response
    List of Observatories



# 2. /observatory/addFavouriteObservatory/
This API endpoint allows users to add observatory to favoutire list. Users must provide the observatory name, and they can include an optional comment.
TOKEN is requaired!

## Request

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

# 3.  /createObservatory/

    This document provides information about the Observatory API, which allows you to create observatories. Observatories are locations with various properties for astronomical observations. This API supports creating observatories with the specified attributes.
    
    TOKEN is requaired!


## Request

- **Method**: POST
- **URL**: `/observatory/create/`

## Request Parameters

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

## Example Requests

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

# 4.  /observatory/update/

    This document provides information about the Update Observatory API, which allows users to update observatory information. Observatories are locations with various properties for astronomical observations. This API supports updating observatory attributes.

    TOKEN is requaired!
## Request

- **Method**: POST
- **URL**: `/observatory/update/`


## Request Parameters

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

## Example Requests

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

# 5. /observatory/getFavouriteObservatory/

    This document provides information about the Observatory API, which allows you to get favourite observatory.
    TOKEN is requaired!

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

## Example Request

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

# 6. /observatory/deleteFavouriteObservatory/

    This document provides information about the Delete Favourite Observatory API, which allows users to delete favourite observatory records based on the observatory name.
    TOKEN is requaired!
## Request

- **Method**: DELETE
- **URL**: `/observatory/deleteFavouriteObservatory/`


## Request Parameters

The request to delete an observatory matrix record should include the following parameter in the request body:

- `observatory` (string, required): The name or identifier of the observatory for which you want to delete the matrix record.

### Example Request Body

```json
{
    "observatory": "My Observatory"
}
```

## Example Request

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