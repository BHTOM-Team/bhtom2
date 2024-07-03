import argparse
import requests

def create_observatory(name, lon, lat,camera_name, calibration_flg, example_file, comment, token,):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    data = {
        "name": name,
        "lon": lon,
        "lat": lat,
        "camera_name": camera_name,
        "calibration_flg": calibration_flg,
        "example_file": example_file,
        "comment": comment,
    }
    api_url=

    response = requests.post(api_url, headers=headers, json=data)
    print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an observatory using the API.")
    parser.add_argument("--name", required=True, help="Name of the observatory")
    parser.add_argument("--lon", required=True, type=float, help="Longitude coordinate")
    parser.add_argument("--camera_name", required=True, type=float, help="Name of the camera")
    parser.add_argument("--lat", required=True, type=float, help="Latitude coordinate")
    parser.add_argument("--calibration_flg", action="store_true", help="Flag for calibration purposes")
    parser.add_argument("--example_file", help="Example file associated with the observatory")
    parser.add_argument("--comment", help="Additional comments or notes")
    parser.add_argument("--token", required=True, help="Authentication token")

    args = parser.parse_args()

    create_observatory(
        args.name,
        args.lon,
        args.lat,
        args.camera_name,
        args.calibration_flg,
        args.example_file,
        args.comment,
        args.token,
    )
