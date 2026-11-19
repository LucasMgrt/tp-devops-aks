r"""Application de démonstration pour le TP DevOps.

  _____ ____    ____              ___                 _    _  ______
 |_   _|  _ \  |  _ \  _____   __/ _ \ _ __  ___     / \  | |/ / ___|
   | | | |_) | | | | |/ _ \ \ / / | | | '_ \/ __|   / _ \ | ' /\___ \
   | | |  __/  | |_| |  __/\ V /| |_| | |_) \__ \  / ___ \| . \ ___) |
   |_| |_|     |____/ \___| \_/  \___/| .__/|___/ /_/   \_\_|\_\____/
                                      |_|

  Lucas MAGRET | ESME | Services Cloud | Sopra Steria
"""
import os
import socket

from flask import Flask, jsonify

from calendrier import est_bissextile

__author__ = "Lucas MAGRET"
__school__ = "ESME | Majeure Transformations Digitales | INGE3"
__module__ = "Services Cloud | TP DevOps : de Git à Kubernetes sur Azure AKS"
__version__ = "1.0.0"

app = Flask(__name__)


@app.get("/")
def accueil():
    return jsonify(
        message=os.getenv("MESSAGE", "Bonjour depuis AKS !"),
        version=os.getenv("APP_VERSION", "dev"),
        pod=socket.gethostname(),
    )


@app.get("/health")
def health():
    """Sonde de vivacité (liveness)."""
    return jsonify(status="ok")


@app.get("/ready")
def ready():
    """Sonde de disponibilité (readiness)."""
    return jsonify(status="ready")


@app.get("/bissextile/<int:annee>")
def bissextile(annee):
    """Indique si une année est bissextile (calendrier grégorien)."""
    return jsonify(annee=annee, bissextile=est_bissextile(annee))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
