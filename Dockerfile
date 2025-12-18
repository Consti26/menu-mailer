FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# TZ pour Europe/Paris et gestion été/hiver
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dossier persistant pour credentials/token/logs
RUN mkdir -p /app/data

# Copie des scripts
COPY main.py oauth_setup.py ./

# Par défaut
ENV TZ=Europe/Paris

CMD ["python", "main.py"]

