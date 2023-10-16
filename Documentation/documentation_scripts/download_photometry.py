import requests
import argparse  

def download_photometry_request(auth_token, name):
    # Define the request body as a Python dictionary
    request_body = {
        "name": name,
    }

    # Define headers
    headers = {
        'accept': 'application/json',
        'Authorization': f'Token {auth_token}',  ## you can hard-code your token here as well
        'Content-Type': 'application/json',
        'X-CSRFToken': 'uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr'
    }
    api_url =  "https://bh-tom2.astrolabs.pl/targets/download-photometry/"
    
    # Send the POST request
    response = requests.post(api_url, json=request_body, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        # Check if response is not empty
        if response.text:
            print(response.text)
        else:
            print("Empty Response")    
    else:
        print(f"Request for {name} failed with status code {response.status_code}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download photometry (magnitudes) from BHTOM")
    parser.add_argument("auth_token", type=str, help="Authentication Token")  #remove this line if you hard-coded the token above
    parser.add_argument("name", type=str, help="Name or id of the target to download")
  
    args = parser.parse_args()
    # Call the function with provided arguments
    download_photometry_request(args.auth_token, args.name)