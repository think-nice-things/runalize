#!/usr/bin/env python3

import argparse
import os
import json
import requests
from pathlib import Path
import pyperclip

def load_token(config_file, silent = False):
    """Load the token from the configuration file."""
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            if not silent:
                print(f"Token loaded from {config_file}.")
            return config.get("token")
    except FileNotFoundError:
        print(f"Configuration file not found at {config_file}.")
        print("Please create the configuration file with your API token.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Configuration file at {config_file} is not valid JSON.")
        exit(1)

def save_token(config_file, token, silent = False):
    """Save the token to the configuration file."""
    config_dir = Path(config_file).parent
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump({"token": token}, f)
    if not silent:
        print(f"Token saved to {config_file}.")

def verify_upload(queue_id, token, silent=False):

    API_ACTIVITIES_URL = "https://runalyze.com/api/v1/activities/uploads"
    """Verify the upload using the queue_id."""
    verification_url = f"{API_ACTIVITIES_URL}/{queue_id}"
    headers = {"token": token}
    
    if not silent:
        print(f"Verifying upload with queue_id: {queue_id}")

    try:
        response = requests.get(verification_url, headers=headers)

        if response.status_code == 200 or response.status_code == 201:
            verification_data = response.json()
            if verification_data.get("status") == "successfully imported":
                activity_id = verification_data.get("activity_id")
                activity_url = f"https://runalyze.com/activity/{activity_id}"
                if not silent:
                    print(f"{activity_url}")
                
                # Copy to clipboard
                pyperclip.copy(activity_url)
            else:
                print(f"Verification failed. Status: {verification_data.get('status')}")
        else:
            print(f"Failed to verify upload. HTTP Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during verification: {e}")

def upload_file(file_path, token, dryrun=False, silent=False):

    API_ACTIVITIES_URL = "https://runalyze.com/api/v1/activities/uploads"

    if not silent:
        print(f"Uploading file: {file_path}")

    if dryrun:
        return

    payload = {"token": token}

    try:
        with open(file_path, "rb") as file:
            files = {
                "file": (os.path.basename(file_path), file, "application/octet-stream")
            }
            response = requests.post(API_ACTIVITIES_URL, headers=payload, files=files)

        if response.status_code == 200 or response.status_code == 201:

            upload_data = response.json()
            if not silent:
                print(f"Successfully uploaded: {file_path}")
                print(f"Response: {upload_data}")
            
            # Verify upload using queue_id
            queue_id = upload_data.get("queue_id")
            if queue_id:
                verify_upload(queue_id, token, silent=silent)
            else:
                print(f"No queue_id returned. Unable to verify upload.")

        else:
            print(f"Failed to upload {file_path}. HTTP Status Code: {response.status_code}")
            if not silent:
                print(f"Response: {response.text}")
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def main():

    config_file = Path.home() / ".config" / "runalyze" / "config.json"

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Upload FIT or GPX files to Runalyze.",
        epilog="Configuration file must contain a JSON object with the key 'token'."
    )
    parser.add_argument(
        "files", metavar="FILE", nargs="*", help="FIT or GPX files to upload"
    )
    parser.add_argument(
        "-n", "--dryrun", action="store_true", help="Perform a dry run without uploading"
    )
    parser.add_argument(
        "-s", "--silent", action="store_true", help="Suppress non-critical output"
    )
    parser.add_argument(
        "-t", "--token", help="Provide the API token directly. If the configuration file does not exist, it will be created."
    )
    parser.add_argument(
        "-c", "--config", help=f'Specify a custom configuration file (default: {config_file})'
    )
    parser.add_argument(
        "-V", "--verify", metavar = 'id', help="verify the upload using the queue_id"
    )
    
    # Parse arguments
    args = parser.parse_args()

    # use supplied config file instead of default
    if args.config:
        config_file = Path(args.config)

    # Handle token
    if args.token:
        token = args.token
        if not config_file.exists():
            save_token(config_file, token, silent = args.silent)
    else:
        token = load_token(config_file, silent = args.silent)

    # set up clipboard
    if "DISPLAY" in os.environ.keys():
        pyperclip.set_clipboard("xclip")

    # Verify upload
    if args.verify:
        verify_upload(args.verify, token, silent=args.silent)
        exit(0)

    # Validate files
    if not args.files:
        print("No files specified for upload. Use -h for help.")
        exit(1)

    # Process files
    for file_path in args.files:
        upload_file(file_path, token, dryrun=args.dryrun, silent=args.silent)

if __name__ == "__main__":
    main()
