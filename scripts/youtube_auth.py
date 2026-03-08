"""OAuth2 authentication flow for YouTube API.

Run this once to generate credentials:
    python scripts/youtube_auth.py

Requires client_secret.json from Google Cloud Console.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import settings

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CLIENT_SECRET_FILE = Path(__file__).parent.parent / "config" / "client_secret.json"
CREDENTIALS_OUTPUT = Path(settings.output_dir) / ".youtube_credentials.json"


def main():
    if not CLIENT_SECRET_FILE.exists():
        print(f"ERROR: {CLIENT_SECRET_FILE} not found.")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials")
        print("Create an OAuth 2.0 Client ID (Desktop app type)")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    credentials = flow.run_local_server(port=8080)

    CREDENTIALS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    creds_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    with open(CREDENTIALS_OUTPUT, "w") as f:
        json.dump(creds_data, f, indent=2)

    print(f"Credentials saved to: {CREDENTIALS_OUTPUT}")
    print("You can now use the upload command.")


if __name__ == "__main__":
    main()
