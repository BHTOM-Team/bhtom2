import requests
import argparse
import os

def upload_files(token, target, data_product_type, files, match_dist=None, comment=None, dry_run=False, no_plot=False, mjd=None, group=None, observer=None):
    headers = {
        'Authorization': f'Token {token}'
    }

    data = {
        'target': target,
        'data_product_type': data_product_type,
        'match_dist': match_dist,
        'comment': comment,
        'dry_run': dry_run,
        'no_plot': no_plot,
        'mjd': mjd,
        'group': group,
        'observer': observer
    }
    "url to upload service"
    api_url=

    response = requests.post(api_url, headers=headers, json=data, files=files)

    print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload files to BHTOM2 API")
    parser.add_argument("token", type=str, help="Authentication token")
    parser.add_argument("target", type=str, help="Target of the uploaded files")
    parser.add_argument("data_product_type", type=str, help="Type of data product")
    parser.add_argument("files", type=str, help="Comma-separated list of files to upload")
    parser.add_argument("--match_dist", type=float, help="Matching distance")
    parser.add_argument("--comment", type=str, help="Additional comment")
    parser.add_argument("--dry_run", action="store_true", help="Dry run mode (true or false)")
    parser.add_argument("--no_plot", action="store_true", help="Disable plot generation (true or false)")
    parser.add_argument("--mjd", type=float, help="Modified Julian Date")
    parser.add_argument("--group", type=str, help="Group associated with the files")
    parser.add_argument("--observer", type=str, help="Observer's name")

    args = parser.parse_args()

    # Split the comma-separated list of files into a list
    files_list = [f.strip() for f in args.files.split(",")]

    upload_files(args.token, args.target, args.data_product_type, files_list,
                 args.match_dist, args.comment, args.dry_run, args.no_plot, args.mjd, args.group, args.observer)
