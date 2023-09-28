import requests
import argparse

def get_catalogs(token):
    headers = {
        'Authorization': f'Token {token}'
    }
    # change url to bhtom2 url
    api_url = 'http://127.0.0.1:8000/calibration/get-catalogs/'
    response = requests.get(api_url, headers=headers)
    print(response.json())
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve catalogs from the BHTOM2 API")
    parser.add_argument("token", type=str, help="Authentication token")

    args = parser.parse_args()

    get_catalogs(args.token)
