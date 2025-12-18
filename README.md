# 📧 Menu Mailer

Système d'envoi automatique d'emails hebdomadaires avec menus + liste de course générés par Mammouth AI via l'API Gmail.

---

## 🚀 Choix d'installation

Ce projet propose **deux modes d'exécution** :

### 🏠 **Mode 1 : Exécution locale avec Docker**
- Conteneur Docker qui tourne en continu sur votre machine/serveur
- Scheduler intégré (APScheduler) pour envoi automatique chaque vendredi 10h30
- Nécessite Docker Desktop et une machine allumée en permanence

### ☁️ **Mode 2 : Automatisation avec GitHub Actions**
- Exécution cloud gratuite (2000 min/mois sur GitHub)
- Aucune machine locale requise
- Configuration via GitHub Secrets

---

## 🏠 Installation - Mode Docker Local

### Architecture des fichiers

```
menu-mailer/
├─ Dockerfile                      # Image Python slim + dépendances
├─ docker-compose.yml              # Configuration du conteneur
├─ requirements.txt                # Dépendances Python
├─ .env                            # Variables sensibles (NON COMMITÉ)
├─ .env.example                    # Template de configuration
├─ .gitignore                      # Exclusions Git
├─ main.py                         # Script principal avec scheduler
├─ oauth_setup.py                  # Génération du token OAuth pour connexion à gmail
├─ data/                           # Volume monté dans le conteneur
│  ├─ credentials.json             # ID client OAuth (Google Cloud)
│  ├─ credentials_encoded.txt      # ID client OAuth (Google Cloud) encodé base64
│  ├─ token.json                   # Token généré après consentement
│  ├─ token_encoded.txt            # Token généré après consentement
│  └─ logs/                        # Logs persistants (optionnel)
└─ README.md
```

### Rôle des fichiers

| Fichier | Description | Obligatoire |
|---------|-------------|-------------|
| `Dockerfile` | Construit l'image Python, installe les dépendances, lance `main.py` | ✅ |
| `docker-compose.yml` | Orchestre le conteneur, charge `.env`, monte le volume `./data`, restart automatique | ✅ |
| `requirements.txt` | Liste des dépendances (requests, APScheduler, google-api-python-client) | ✅ |
| `.env` | Variables sensibles (clés API, emails) - **À créer localement, ne jamais commiter** | ✅ |
| `.env.example` | Template avec valeurs factices pour documenter les variables requises | ✅ |
| `.gitignore` | Ignore `data/`, `.env`, `__pycache__/` pour ne pas commiter de secrets | ✅ |
| `main.py` | Scheduler APScheduler : planifie l'envoi tous les vendredis 10h30 (Europe/Paris), appelle l'API Mammouth AI, formate l'email, envoie via Gmail API | ✅ |
| `oauth_setup.py` | Script d'initialisation OAuth : lit `credentials.json`, ouvre le navigateur pour consentement Google, génère `token.json` avec refresh token | ✅ |
| `data/credentials.json` | Identifiant client OAuth Desktop téléchargé depuis Google Cloud Console | ✅ |
| `data/token.json` | Refresh token généré après authentification (permet l'envoi d'emails sans interaction) | ✅ |
| `data/logs/` | Dossier pour logs persistants (optionnel) | ⚠️ |

### Prérequis

- Docker Desktop installé
- Compte Google Cloud avec API Gmail activée
- Clé API Mammouth AI

### Installation pas à pas

#### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/menu-mailer.git
cd menu-mailer
```

#### 2. Configurer les variables d'environnement

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

Remplir avec vos valeurs

#### 3. Configurer l'authentification Google

**a) Créer les credentials OAuth (première fois uniquement). /!\ Manière de faire valable au moment du projet. Vérifiez en ligne si le process est le meme.**

1. Aller sur [Google Cloud Console](https://console.cloud.google.com)
2. Créer un projet ou sélectionner un existant
3. Activer l'API Gmail (`APIs & Services` → `Enable APIs`)
4. Créer un identifiant OAuth (`Credentials` → `Create Credentials` → `OAuth client ID`)
5. Type : **Application de bureau / Desktop app**
6. Télécharger le JSON et le placer dans `data/credentials.json`

**b) Générer le token d'authentification**

```bash
# Installer les dépendances localement
pip install -r requirements.txt

# Lancer le script d'authentification
python oauth_setup.py
```

→ Un navigateur s'ouvre, connectez-vous avec votre compte Gmail  
→ Accordez les permissions  
→ Le fichier `data/token.json` est généré automatiquement

#### 4. Démarrer le conteneur Docker

```bash
# Démarrer Docker Desktop
open -a Docker  # macOS
# ou lancer manuellement l'application

# Construire et lancer le conteneur en arrière-plan
docker compose up -d --build menu-mailer
```

#### 5. Vérifier le fonctionnement

```bash
# Voir les logs en temps réel
docker compose logs -f menu-mailer

# Vérifier le statut
docker compose ps
```

### Commandes utiles

```bash
# Arrêter le conteneur
docker compose down

# Redémarrer après modification
docker compose up -d --build

# Supprimer l'image
docker image rm menu-mailer-menu-mailer

# Accéder au shell du conteneur
docker compose exec menu-mailer sh
```

---

## ☁️ Installation - Mode GitHub Actions

### Architecture des fichiers

```
menu-mailer/
├─ .github/
│  └─ workflows/
│     └─ weekly-menu.yml   # Workflow GitHub Actions (cron + déclenchement manuel)
├─ requirements.txt        # Dépendances Python
├─ .env.example            # Documentation des variables
├─ .gitignore              # Exclusions Git
├─ main.py                 # Script d'envoi unique 
└─ README.md
```

### Fichiers NON nécessaires en mode GitHub Actions

| Fichier | Raison |
|---------|--------|
| `Dockerfile` | GitHub Actions exécute Python directement |
| `docker-compose.yml` | Pas de conteneur dans le workflow |
| `.env` | Remplacé par GitHub Secrets |
| `oauth_setup.py` | Impossible d'ouvrir un navigateur sur GitHub |
| `data/` | Credentials stockés en GitHub Secrets |

### Installation pas à pas

#### 1. Générer le token OAuth en local (une seule fois)

⚠️ **Obligatoire** : GitHub Actions ne peut pas ouvrir de navigateur, vous devez générer `token.json` localement d'abord.

```bash
# En local sur votre machine
pip install google-auth google-auth-oauthlib google-auth-httplib2
python oauth_setup.py
```

→ Suit le processus d'authentification Google  
→ `data/token.json` est créé

#### 2. Configurer les GitHub Secrets

Aller dans votre repository GitHub :  
**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Créer toutes les secrets sur fichier .env.example.

**Copier le contenu des fichiers :**

```bash
# Afficher le contenu à copier-coller
cat data/credentials.json
cat data/token.json
```

#### 3. Pousser le code sur GitHub

```bash
git add .github/ send_menu.py requirements.txt
git commit -m "Setup GitHub Actions workflow"
git push origin main
```

#### 4. Tester le workflow

**Option 1 : Déclenchement manuel**

1. Aller dans l'onglet **Actions** de votre repository
2. Cliquer sur **Weekly Menu Sender**
3. Cliquer sur **Run workflow** → **Run workflow**

**Option 2 : Attendre le cron**

Le workflow s'exécutera lors du lancement, puis automatiquement tous les vendredis à 10h30 (heure de Paris).

#### 5. Consulter les logs

Dans l'onglet **Actions**, cliquez sur une exécution pour voir :
- Les étapes détaillées
- Les éventuelles erreurs
- La confirmation d'envoi

---

## 🔀 Comparaison des modes

| Critère | Docker Local | GitHub Actions |
|---------|-------------|----------------|
| **Machine requise** | Serveur/NAS/PC allumé 24/7 | Aucune |
| **Coût** | Électricité locale | Gratuit (2000 min/mois) |
| **Scheduler** | APScheduler dans `main.py` | Cron GitHub (`weekly-menu.yml`) |
| **Secrets** | Fichier `.env` local | GitHub Secrets (chiffrés) |
| **OAuth** | `oauth_setup.py` + navigateur | Token pré-généré en local puis stocké |
| **Logs** | `docker compose logs` | Interface web GitHub Actions |
| **Maintenance** | Mise à jour Docker/dépendances manuelles | GitHub gère l'infra |
| **Complexité setup** | Moyenne (Docker + OAuth) | Faible (juste secrets à configurer) |
| **Déclenchement manuel** | Relancer le conteneur | Bouton "Run workflow" |

---

### Personnaliser le prompt Mammouth AI

Éditer la fonction dans `main.py` ou `send_menu.py` :

```python
json={
    'prompt': 'Génère un menu végétarien de la semaine avec recettes détaillées',
    'temperature': 0.7,  # Créativité (0-1)
    'max_tokens': 1000
}
```

---

## 📊 Recommandation d'usage

**Utilisez le mode Docker si :**
- Vous avez un serveur/NAS personnel
- Vous voulez un contrôle total sur l'exécution
- Vous gérez déjà d'autres conteneurs Docker

**Utilisez GitHub Actions si :**
- Vous n'avez pas de serveur dédié
- Vous voulez une solution zéro maintenance
- Vous préférez une infra cloud gérée

