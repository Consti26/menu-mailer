import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

DATA = Path("data"); DATA.mkdir(exist_ok=True)
CRED = DATA/"credentials.json"
TOK  = DATA/"token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

port = int(os.getenv("OAUTH_PORT", "8080"))
flow = InstalledAppFlow.from_client_secrets_file(str(CRED), SCOPES)

# En Docker Linux + --network host: OK
# En macOS/Windows: fais cette étape hors Docker pour générer token.json
creds = flow.run_local_server(host="localhost", port=port, open_browser=False)

TOK.write_text(creds.to_json())
print(f"Token écrit: {TOK}")
