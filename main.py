import os
import json
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any

import openai
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Optionnel: charge .env en local
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --------- Config / Constantes ---------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TOKEN_PATH = DATA_DIR / "token.json"
CREDENTIALS_PATH = DATA_DIR / "credentials.json"

# OpenAI compatible (Mammouth.ai)
openai.api_base = os.getenv("MAMMOTH_API_BASE") or os.getenv("MAMMOUTH_API_BASE") or "https://api.mammouth.ai/v1"
openai.api_key = os.getenv("MAMMOTH_API_KEY") or os.getenv("MAMMOUTH_API_KEY")
MODEL_NAME = os.getenv("MAMMOTH_MODEL") or os.getenv("MAMMOUTH_MODEL") or "gpt-4.1"

# Emails
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECIPIENT_EMAILS = [e.strip() for e in (os.getenv("RECIPIENT_EMAILS") or "").split(",") if e.strip()]

# TZ
TZ = os.getenv("TZ", "Europe/Paris")
PARIS_TZ = pytz.timezone(TZ)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# --------- Aide JSON ---------
def extract_json(text: str) -> str:
    """
    Extrait un JSON brut s'il est encapsulé dans des fences ```json ... ```.
    """
    if not text:
        return text
    text = text.strip()
    if text.startswith("```"):
        # Cherche le premier bloc code
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
    return text

# --------- Appel Mammouth.ai (OpenAI compatible) ---------
def fetch_menu() -> Dict[str, Any]:
    """
    Interroge le modèle via Mammouth.ai pour générer 10 plats avec:
    - title
    - description
    - time_minutes (int)
    - ingredients_for_two (liste de chaînes)
    Retourne un dict {"dishes": [...]}
    """
    assert openai.api_key, "MAMMOUTH_API_KEY manquant dans l'environnement."

    system_msg = {
        "role": "system",
        "content": (
            "Tu es un assistant culinaire qui génère des menus en français. "
            "RETOURNE UNIQUEMENT un JSON valide, sans aucun texte hors JSON. "
            'Schéma attendu: {"dishes": [ { "title": str, "description": str, "time_minutes": int, "ingredients_for_two": [str, ...] }, ... (10 éléments) ] }'
        )
    }

    user_msg = {
        "role": "user",
        "content": (
            "Génère une liste de 10 plats variés pour la semaine. "
            "Pour CHAQUE plat, fournis: title, description, time_minutes (durée totale en minutes), "
            "ingredients_for_two (liste d'ingrédients pour 2 personnes). "
            "Propose majoritairement des plats de saison. "
            "Tous les plats doivent contenir suffisament de proteines (minimum 10g de proteine par personne) "
            "Langue: français. Réponds STRICTEMENT en JSON conforme au schéma."
        )
    }

    logging.info("Appel Mammouth.ai (modèle: %s)...", MODEL_NAME)
    resp = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[system_msg, user_msg],
        temperature=0.7,
        stream=False  # simple pour ce cas
    )

    content = resp.choices[0].message["content"]
    content = extract_json(content)

    try:
        data = json.loads(content)
        # Validations minimales
        dishes = data.get("dishes", [])
        if not isinstance(dishes, list) or len(dishes) == 0:
            raise ValueError("Réponse JSON inattendue: 'dishes' vide ou non-liste.")
        # Normalisation des types
        for d in dishes:
            if "time_minutes" in d:
                try:
                    d["time_minutes"] = int(d["time_minutes"])
                except Exception:
                    pass
        return {"dishes": dishes[:10]}
    except Exception as e:
        logging.exception("Échec de parsing JSON depuis le modèle: %s", e)
        raise

# --------- Mise en forme email ---------
def build_email_subject(dishes: List[Dict[str, Any]]) -> str:
    return f"Menu de la semaine — 10 idées de plats pour 2 personnes"

def build_email_text(dishes: List[Dict[str, Any]]) -> str:
    lines = ["Voici 10 idées de plats pour 2 personnes:\n"]
    for i, d in enumerate(dishes, start=1):
        title = d.get("title", f"Plat {i}")
        desc = d.get("description", "")
        tmin = d.get("time_minutes", "")
        ings = d.get("ingredients_for_two", [])
        if isinstance(ings, list):
            ings_txt = ", ".join(ings)
        else:
            ings_txt = str(ings)
        lines.append(f"{i}. {title}\n   - Description: {desc}\n   - Durée: {tmin} min\n   - Ingrédients (x2): {ings_txt}\n")
    return "\n".join(lines)

def build_email_html(dishes: List[Dict[str, Any]]) -> str:
    items = []
    for i, d in enumerate(dishes, start=1):
        title = d.get("title", f"Plat {i}")
        desc = d.get("description", "")
        tmin = d.get("time_minutes", "")
        ings = d.get("ingredients_for_two", [])
        if isinstance(ings, list):
            ings_html = "".join(f"<li>{ing}</li>" for ing in ings)
        else:
            ings_html = f"<li>{ings}</li>"
        items.append(f"""
        <li style="margin-bottom:12px;">
          <strong>{i}. {title}</strong><br/>
          <em>{desc}</em><br/>
          <span>Durée: {tmin} min</span>
          <ul>{ings_html}</ul>
        </li>
        """)
    html = f"""
    <html>
      <body>
        <p>Voici 10 idées de plats pour 2 personnes :</p>
        <ol>
          {''.join(items)}
        </ol>
        <p style="color:#777;font-size:12px;">Envoi automatique hebdomadaire.</p>
      </body>
    </html>
    """
    return html

# --------- Gmail API ---------
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    if not TOKEN_PATH.exists():
        raise FileNotFoundError("data/token.json introuvable. Exécute d'abord oauth_setup.py en local.")

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            logging.info("Actualisation du token Gmail...")
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("Identifiants Gmail invalides. Relance oauth_setup.py.")
    service = build("gmail", "v1", credentials=creds)
    return service

def create_mime_message(subject: str, text: str, html: str, sender: str, recipients: List[str]):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    part1 = MIMEText(text, "plain", "utf-8")
    part2 = MIMEText(html, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)
    return msg

def send_email_gmail_api(subject: str, text: str, html: str):
    assert SENDER_EMAIL, "SENDER_EMAIL manquant"
    assert RECIPIENT_EMAILS, "RECIPIENT_EMAILS manquant"
    service = get_gmail_service()
    msg = create_mime_message(subject, text, html, SENDER_EMAIL, RECIPIENT_EMAILS)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {"raw": raw}
    try:
        sent = service.users().messages().send(userId="me", body=body).execute()
        logging.info("Email envoyé (id: %s)", sent.get("id"))
    except HttpError as e:
        logging.exception("Erreur Gmail API: %s", e)
        raise

# --------- Job principal ---------
def job_run():
    logging.info("Début du job hebdomadaire.")
    data = fetch_menu()
    dishes = data.get("dishes", [])[:10]
    subject = build_email_subject(dishes)
    text = build_email_text(dishes)
    html = build_email_html(dishes)
    send_email_gmail_api(subject, text, html)
    logging.info("Job terminé avec succès.")

# --------- Scheduler ---------
def main():
    # Vérifs de base
    if not openai.api_key:
        raise RuntimeError("MAMMOUTH_API_KEY manquant.")
    if not CREDENTIALS_PATH.exists():
        logging.warning("data/credentials.json manquant (utile si tu dois régénérer le token).")
    if not TOKEN_PATH.exists():
        logging.warning("data/token.json manquant. Lance oauth_setup.py en local puis copie le token ici.")

    # ===== DÉTECTION GITHUB ACTIONS =====
    is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"
    run_immediately = os.getenv("RUN_IMMEDIATELY", "false").lower() == "true"

    if is_github_actions or run_immediately:
        # Mode one-shot : exécution immédiate puis exit
        logging.info("Mode exécution immédiate (GitHub Actions ou RUN_IMMEDIATELY=true)")
        job_run()
        logging.info("Exécution terminée. Arrêt du programme.")
        exit(0)
        return  # Sort de main() sans démarrer le scheduler
    
    # ===== MODE LOCAL (inchangé) =====
    logging.info("Mode local : démarrage du scheduler continu")
    sched = BlockingScheduler(timezone=PARIS_TZ)
    # Tous les vendredis 10:30 Europe/Paris
    trigger = CronTrigger(day_of_week="fri", hour=10, minute=30, timezone=PARIS_TZ)
    sched.add_job(job_run, trigger=trigger, id="weekly_menu_email", replace_existing=True)
    logging.info("Scheduler démarré. Prochain envoi: chaque vendredi à 10:30 (%s).", TZ)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Arrêt demandé.")

if __name__ == "__main__":
    main()
