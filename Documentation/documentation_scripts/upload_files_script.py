import os
import requests

# The directory containing all the necessary fits files
directory = '### DIRECTORY NAME ###'

token= '### Yours Token ###'
target_name = '### TARGET NAME ###'
observatory_name= '### Observatory name ###'
filter_name = '### FILTER NAME ###'

data_product_type = 'fits_file'

# Dry run option should be set to "True" or "False" (as a string)
dry_run = '### DRY RUN ###'
comment = '### comment ###'
for filename in os.listdir(directory):
    with open(os.path.join(directory, filename), 'rb') as f:
        print("Sending...")
        response = requests.post(
            url='https://uploadsvc2.astrolabs.pl/upload/',
            headers={
                'Authorization': "Token " + str(token)
            },
            data={
                'target': target_name,
                'filter': filter_name,
                'data_product_type': data_product_type,
                'dry_run': dry_run,
                'observatory': observatory_name,
                'comment': comment,
            },
            files={'files': f}
        )
        print(response.json())