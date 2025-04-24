import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import datetime

# 🔐 Kirjutame secretsist .json-iks (ainult ajutiselt runtime ajal)
SERVICE_JSON = "service_account.json"
with open(SERVICE_JSON, "w") as f:
    json.dump(dict(st.secrets["google_service"]), f)  # <- fixitud rida


SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_ID = "1BdOatFcuxghS3sI7nqwdUUfom35aY-vM"

def upload_to_drive(filepath):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_JSON, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)

    filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID]
    }
    media = MediaFileUpload(filepath, mimetype="application/zip")

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return uploaded.get("id"), filename