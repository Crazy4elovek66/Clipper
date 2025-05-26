import os
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.json"
CLIENT_SECRET_FILE = "client_secret.json"



if not os.path.exists("client_secret.json") and os.getenv("GOOGLE_CLIENT_SECRET_JSON"):
    with open("client_secret.json", "w") as f:
        f.write(os.getenv("GOOGLE_CLIENT_SECRET_JSON"))

def authenticate_youtube():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str = "#shorts #twitch",
    tags: Optional[List[str]] = None,
    privacy_status: str = "public"
):
    youtube = authenticate_youtube()
    if title.lower().startswith("vertical "):
        title = title[9:].strip()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or ["shorts", "twitch"]
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print(f"Upload complete: https://youtu.be/{response['id']}")
    return response['id']