# TP DevOps AKS | Lucas MAGRET | ESME INGE3
# 1 : image de base Python 3.12 légère (variante "slim")
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2 : utilisateur système non-root d'UID 10001
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app

# 3 : répertoire de travail
WORKDIR /app

# 4 : dépendances d'abord (couche en cache tant que requirements.txt ne bouge pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5 : code applicatif
COPY app.py calendrier.py ./

# Version de l'application injectée au build (utile en Partie 3)
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# 6 : UID 10001 numérique, vérifiable par runAsNonRoot
USER 10001

# 7 : port documenté
EXPOSE 8080

# Commande de l'exploitation corrigée (incident n°1) : 0.0.0.0 et non 127.0.0.1
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
