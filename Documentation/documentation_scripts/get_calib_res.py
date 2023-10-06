import requests
import argparse  

def send_calibration_request(auth_token, files, get_plot=True):
    # Convert string file_ids to integers
    files = [int(file) if file.isdigit() else file for file in files]

    # Define the request body as a Python dictionary
    request_body = {
        "files": files,
        "getPlot": get_plot
    }

    # Define headers
    headers = {
        'accept': 'application/json',
        'Authorization': f'Token {auth_token}',
        'Content-Type': 'application/json',
        'X-CSRFToken': 'uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr'
    }
    api_url =  "https://bh-tom2.astrolabs.pl/calibration/get-calibration-res/"
        # Send the POST request
    response = requests.post(api_url, json=request_body, headers=headers)
    print(response.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a calibration request to the API.")
    parser.add_argument("auth_token", type=str, help="Authentication Token")
    parser.add_argument("files", type=str, nargs="+", help="Files(as space-separated integers or strings)")
  
    parser.add_argument("--get_plot", action="store_true", help="Get Plot (default: True)")

    args = parser.parse_args()

    # Call the function with provided arguments
    send_calibration_request(args.auth_token, args.files, args.get_plot)