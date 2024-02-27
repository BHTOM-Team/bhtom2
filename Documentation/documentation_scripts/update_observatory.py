import argparse
import requests

def update_observatory(name, token, update_data):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    data = {
        "name": name,
        **update_data  # Include other update fields here
    }
    api_url=
    response = requests.patch(api_url, headers=headers, json=data)
    print(response.json())
   
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update an observatory using the API.")
    parser.add_argument("--name", required=True, help="Name of the observatory")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument("--lon", type=float, help="New longitude coordinate")
    parser.add_argument("--lat", type=float, help="New latitude coordinate")
    parser.add_argument("--calibration_flg", action="store_true", help="Flag for calibration purposes")
    parser.add_argument("--comment", help="New additional comments or notes")

    args = parser.parse_args()

    update_data = {
        "lon": args.lon,
        "lat": args.lat,
        "calibration_flg": args.calibration_flg,
        "comment": args.comment,
    }

    update_observatory(args.name, args.token, update_data)
