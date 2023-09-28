import argparse
import requests

def get_observatory_matrix(user, active_flg, observatory, created_start, created_end, token):
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    data = {
        "user": user,
        "active_flg": active_flg,
        "observatory": observatory,
        "created_start": created_start,
        "created_end": created_end,
    }
    api_url=
    response = requests.post(api_url, headers=headers, json=data)
    print(response.json())  

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve observatory matrix data using the API.")
    parser.add_argument("--user", help="Filter by user")
    parser.add_argument("--active_flg", type=bool, help="Filter by active flag")
    parser.add_argument("--observatory", help="Filter by observatory")
    parser.add_argument("--created_start", help="Filter by created start datetime")
    parser.add_argument("--created_end", help="Filter by created end datetime")
    parser.add_argument("--token", required=True, help="Authentication token")

    args = parser.parse_args()

    get_observatory_matrix(
        args.user,
        args.active_flg,
        args.observatory,
        args.created_start,
        args.created_end,
        args.token,
    )
