menu-mailer/
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ .env                 # variables locales (non commitées)
├─ .env.example         # modèle sans secrets
├─ .gitignore           # pour éviter de commiter les secrets
├─ main.py              # script principal + scheduler (APScheduler)
├─ oauth_setup.py       # script 1-shot pour générer token.json (OAuth) 
├─ data/                # volume monté dans le conteneur /app/data
│  ├─ credentials.json  # (fourni par Google Cloud, type OAuth Desktop)
│  ├─ token.json        # (généré par oauth_setup.py après consentement)
│  └─ logs/             # (optionnel) fichiers de logs persistants
└─ README.md            # (optionnel) notes d’installation/usage


Rôle de chaque élément :

Dockerfile: image Python slim + tzdata; installe les dépendances et lance main.py.

docker-compose.yml: définit le service menu-mailer, charge .env, monte ./data dans le conteneur, politique restart: unless-stopped.

requirements.txt: dépendances Python (requests, APScheduler, google-api-python-client, etc.).

.env: vos variables sensibles (MAMMOUTH_API_KEY, emails, etc.). Non commité.

.env.example: même clés que .env mais valeurs factices, pour partager la conf sans secrets.

.gitignore: ignore data/, .env, __pycache__/, etc.

main.py: 
planifie une tâche tous les vendredis 10:30 Europe/Paris,
appelle l’API Mammouth AI,
formate le contenu (texte + HTML),
envoie l’email via l’API Gmail (refresh token).

oauth_setup.py:
lit data/credentials.json (ID client OAuth “Desktop”),
ouvre un navigateur pour le consentement,
enregistre data/token.json (avec refresh token).
--> c'est le script 2 qui a fonctionné, en lançant le script tout seul après avoir pip install manuellement quelques librairies

data/:
credentials.json: téléchargé depuis Google Cloud (OAuth client Desktop),

token.json: généré par oauth_setup.py après login/consentement,

logs/: dossiers/fichiers de logs persistants si vous activez une écriture de logs.


COMMAND :
1. Enter the file menu-mailer
2. Switch on Docker 
    either via the list of application
    or run 
        open -a Docker
3. run 
    docker compose up -d --build menu-mailer    # démarre en arrière-plan
optionnel : 
    docker compose logs -f menu-mailer           # voir les logs en continu
    docker compose ps                            # statut
    docker compose down                          # eteidre le conteneur
    docker image rm menu-mailer-menu-mailer      # supprimer l'image 
