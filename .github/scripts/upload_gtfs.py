from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
import datetime
import json
import os

# GTFS settings
GTFS_URL = "https://peatus.ee/gtfs/gtfs.zip"
GTFS_ZIP = "gtfs.zip"
FOLDER_ID = "1BdOatFcuxghS3sI7nqwdUUfom35aY-vM"

# Save GTFS zip
r = requests.get(GTFS_URL)
with open(GTFS_ZIP, "wb") as f:
    f.write(r.content)

# Load secrets from secrets.toml manually
secrets_file = os.path.expanduser("~/.streamlit/secrets.toml")
data = {}
with open(secrets_file) as f:
    for line in f:
        if "=" in line:
            key, val = line.strip().split("=", 1)
            data[key.strip()] = val.strip().strip('"').replace("\\n", "\n")

# Convert to service account dict
credentials_dict = {
    "type": "service_account",
    "project_id": data["project_id"],
    "private_key_id": data["private_key_id"],
    "private_key": data["private_key"],
    "client_email": data["client_email"],
    "client_id": data["client_id"],
    "auth_uri": data["auth_uri"],
    "token_uri": data["token_uri"],
    "auth_provider_x509_cert_url": data["auth_provider_x509_cert_url"],
    "client_x509_cert_url": data["client_x509_cert_url"],
}

# Upload to Google Drive
creds = service_account.Credentials.from_service_account_info(credentials_dict)
service = build("drive", "v3", credentials=creds)
filename = f"gtfs_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.zip"
file_metadata = {"name": filename, "parents": [FOLDER_ID]}
media = MediaFileUpload(GTFS_ZIP, mimetype="application/zip")
file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
print(f"Uploaded file ID: {file.get('id')}")
