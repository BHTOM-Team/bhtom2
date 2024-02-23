import argparse
import requests

def delete_observatory_matrix(observatory,camera, token ):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    data = {
        "observatory": observatory,
        "camera": camera
    }
    api_url = 

    response = requests.delete(api_url, headers=headers, json=data)

    print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete an observatory matrix record using the API.")
    parser.add_argument("--observatory", required=True, help="Name or identifier of the observatory to delete")
    parser.add_argument("--camera", required=True, help="Name or identifier of the observatory camera to delete")
    parser.add_argument("--token", required=True, help="Authentication token")

    args = parser.parse_args()

    delete_observatory_matrix(args.observatory,args.camera, args.token)
