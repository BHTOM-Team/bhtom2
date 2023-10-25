'''
This script reads all files in a directory, assumes they are fits with flatfielded/debiased/darkcorrected images,
and uploads them to BHTOM for photometric processing for a given target.

it also allows uploading cat files (with SExtractor-format photometry), but only one file at a time is allowed and MJD must be provided for that file.

'''

import os
import requests
import argparse

data_product_type = 'fits_file' # fits_file or photometry (instrumental in SExtractor format), photometry_nondetection, spectroscopy. NOTE: that for photometry, mjd field is required

directory = '' # The directory containing all the necessary fits files

target_name = '' #Name of the target as it is listed in the BHTOM target list to which this data will be linked
token= '' # Token obtained from BHTOM/API for a user. This user's name will be associated to the datapoint in the database
observatory_name= '' # Observatory/Facility name to which this datapoint will be associated. 


filter_name = 'GaiaSP/any'  #force filter to which your data should be calibrated, default: 'GaiaSP/any'
dry_run = 'False' #'True' if you just want to test the upload and do not store the observation in the database
comment = '' #comment about the observation, data processing, etc.
mjd = '' # Time of the observation in MJD, only needed for photometry uploads


# Create the parser
parser = argparse.ArgumentParser(description="Process some parameters.")

# Add the parameters
parser.add_argument('--directory', default=None, help='The directory containing all the necessary fits files')
parser.add_argument('--filename', default=None, help='A single file to be processed')
parser.add_argument('--target_name', default='', help='Name of the target as it is listed in the BHTOM target list to which this data will be linked')
parser.add_argument('--token', default='', help='Token obtained from BHTOM/API for a user. This user\'s name will be associated to the datapoint in the database')
parser.add_argument('--observatory_name', default='', help='Observatory/Facility name to which this datapoint will be associated.')
parser.add_argument('--filter_name', default='GaiaSP/any', help='Force filter to which your data should be calibrated, default: \'GaiaSP/any\'')
parser.add_argument('--dry_run', default='False', help='\'True\' if you just want to test the upload and do not store the observation in the database')
parser.add_argument('--comment', default=None, help='Comment about the observation, data processing, etc.')
parser.add_argument('--mjd', default=None, help='Time of the observation in MJD, only needed for photometry uploads')
parser.add_argument('--data_product_type', default='', help='Data product type')
parser.add_argument('--observer', default=None, help='Name of the observer to be associated to the data. Note this overwrites the name from the token, used as default.')

# Parse the arguments
args = parser.parse_args()

# Now you can access the values using args.<parameter_name>
directory = args.directory
filename = args.filename
target_name = args.target_name
token = args.token
observatory_name = args.observatory_name
filter_name = args.filter_name
dry_run = args.dry_run
comment = args.comment
mjd = args.mjd
data_product_type = args.data_product_type
observer = args.observer

# Check if directory or filename is provided
if directory is not None:
    file_list = [os.path.join(directory, f) for f in os.listdir(directory)]
elif filename is not None:
    file_list = [filename]
else:
    print("Please provide either a directory or a filename.")
    exit(1)

for file in file_list:
    with open(file, 'rb') as f:
        print("Sending...")
        
        # Build the data dictionary dynamically
        data = {
            'target': target_name,
            'filter': filter_name,
            'data_product_type': data_product_type,
            'dry_run': dry_run,
            'observatory': observatory_name
        }
        if comment is not None:
            data['comment'] = comment
        if mjd is not None:
            data['mjd'] = mjd
        if observer is not None:
            data['observer'] = observer

        response = requests.post(
            url='https://uploadsvc2.astrolabs.pl/upload/',
            headers={
                'Authorization': "Token " + str(token)
            },
            data=data,
            files={'files': f}
        )
        print(response.json())