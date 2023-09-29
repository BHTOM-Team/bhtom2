import argparse
import requests

def create_target(name, ra, dec, epoch, classification, discovery_date, importance, cadence, token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
    }

    data = {
        "name": name,
        "ra": ra,
        "dec": dec,
        "epoch": epoch,
        "classification": classification,
        "discovery_date": discovery_date,
        "importance": importance,
        "cadence": cadence,
    }
    api_url=
    response = requests.post(api_url,headers=headers, json=data)
    print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new target using the API.")
    parser.add_argument("--name", required=True, help="Name or identifier of the target")
    parser.add_argument("--ra", type=float, required=True, help="Right Ascension (RA) of the target")
    parser.add_argument("--dec", type=float, required=True, help="Declination (Dec) of the target")
    parser.add_argument("--epoch", help="Epoch or reference time of the target")
    parser.add_argument("--classification", help="Classification or type of the target")
    parser.add_argument("--discovery_date", help="Discovery date and time of the target")
    parser.add_argument("--importance", type=int, help="Importance or priority of the target")
    parser.add_argument("--cadence", type=int, help="Cadence or observation frequency of the target")
    parser.add_argument("--token", required=True, help="Authentication token")

    args = parser.parse_args()

    create_target(
        args.name,
        args.ra,
        args.dec,
        args.epoch,
        args.classification,
        args.discovery_date,
        args.importance,
        args.cadence,
        args.token,
    )


