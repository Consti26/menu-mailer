import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_PATH = DATA_DIR / "credentials.json"
TOKEN_PATH = DATA_DIR / "token.json"
print('variables dones')

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("ok data_dir")
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError("data/credentials.json introuvable. Télécharge le client OAuth (type Desktop) depuis Google Cloud.")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    print("ok flow")
    # Mode headless par défaut dans un conteneur
    HEADLESS = os.getenv("OAUTH_HEADLESS", "1") == "1"
    PORT = int(os.getenv("OAUTH_PORT", "8080"))
    print("ok variables headless port")

    if HEADLESS:
        # Copie/colle l'URL dans ton navigateur, puis le code retourné dans le terminal
        creds = flow.run_console()
    else:
        # Démarre un serveur local sans ouvrir de navigateur dans le conteneur
        creds = flow.run_local_server(port=PORT, open_browser=True)

    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"Token enregistré: {TOKEN_PATH}")

if __name__ == "__main__":
    main()