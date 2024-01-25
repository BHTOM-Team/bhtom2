import requests
import argparse

def get_catalogs(token):
    headers = {
        'Authorization': f'Token {token}'
    }
    api_url =  "https://bh-tom2.astrolabs.pl/calibration/get-catalogs/"
    response = requests.get(api_url, headers=headers)
    print(response.json())
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve catalogs from the BHTOM2 API")
    parser.add_argument("token", type=str, help="Authentication token")

    args = parser.parse_args()

    get_catalogs(args.token)
