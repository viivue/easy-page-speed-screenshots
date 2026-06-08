"""One-time: get a Dropbox REFRESH token for unattended use.

The console 'Generate' button gives a SHORT-LIVED token (testing only);
Dropbox retired no-expiration tokens. This offline flow returns a refresh
token that the app trades for fresh access tokens automatically.

Prereq: create the app at https://www.dropbox.com/developers/apps/create
  - Scoped access
  - Full Dropbox  (required: files go into an existing shared team folder)
  - Permissions tab, then Submit: files.content.write, files.content.read,
    sharing.write, sharing.read, files.metadata.read

Run:  python get_dropbox_token.py
"""
import os
from dropbox import DropboxOAuth2FlowNoRedirect

APP_KEY = os.environ.get("DROPBOX_APP_KEY") or input("App key: ").strip()
APP_SECRET = os.environ.get("DROPBOX_APP_SECRET") or input("App secret: ").strip()

SCOPES = [
    "files.content.write",
    "files.content.read",
    "sharing.write",
    "sharing.read",
    "files.metadata.read",
]

flow = DropboxOAuth2FlowNoRedirect(
    APP_KEY, APP_SECRET, token_access_type="offline", scope=SCOPES
)
print("\n1) Open this URL in your browser and click Allow:\n")
print(flow.start())
code = input("\n2) Paste the authorization code Dropbox shows you: ").strip()
result = flow.finish(code)
print("\nDone. Add this line to your .env file:\n")
print("DROPBOX_REFRESH_TOKEN=" + result.refresh_token)