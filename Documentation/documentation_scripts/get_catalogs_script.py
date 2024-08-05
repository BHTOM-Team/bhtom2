import requests
import argparse

def get_catalogs(token, page):
    headers = {
        'Authorization': f'Token {token}'
    }
    api_url =  f'https://bh-tom2.astrolabs.pl/calibration/get-catalogs/?page={page}',
    response = requests.get(api_url, headers=headers)
    print(response.json())
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve catalogs from the BHTOM2 API")
    parser.add_argument("token", type=str, help="Authentication token")
    parser.add_argument("page", type=int, help="Page")

    args = parser.parse_args()

    get_catalogs(args.token, args.page)
