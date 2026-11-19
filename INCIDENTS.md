# Journal des incidents

Auteur : Lucas MAGRET | ESME INGE3 | TP DevOps AKS (Sopra Steria)

## Incident n°1 | Application injoignable depuis l'extérieur du conteneur
- **Partie / étape :** Partie 2 | 2.4 (`docker run` puis `curl -s localhost:8080`)
- **Symptôme observé :** le conteneur est `Up` dans `docker ps`, le port est publié (`0.0.0.0:8080->8080/tcp`), mais `curl -sS localhost:8080` renvoie `curl: (56) Recv failure: Connection reset by peer` (ou `Empty reply from server` selon l'OS). Aucune requête n'apparaît dans les logs.
- **Diagnostic :**
  - `docker logs mon-app` : gunicorn démarre bien, mais affiche `Listening at: http://127.0.0.1:8080`.
  - `docker exec mon-app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').read())"` : répond `{"status":"ok"}`. L'application fonctionne donc **à l'intérieur** du conteneur.
  - `docker inspect mon-app --format '{{json .Config.Cmd}}'` : confirme `--bind 127.0.0.1:8080` dans la commande fournie par l'exploitation.
- **Cause racine :** `127.0.0.1` est la boucle locale **du namespace réseau du conteneur**. Le port publié par Docker (`-p 8080:8080`) arrive sur l'interface `eth0` du conteneur, où personne n'écoute. Même problème attendu sur Kubernetes : les sondes du kubelet et le Service visent l'IP du pod.
- **Correction appliquée :** `Dockerfile`, commande `CMD` passée à `--bind 0.0.0.0:8080` (commit `feat: conteneurisation de l'application`, branche `feat/docker`, PR fusionnée).
- **Comment l'éviter à l'avenir :** dans un conteneur, toujours écouter sur `0.0.0.0` (facteur 12-factor n°7 « liaison de port ») ; tester l'image **depuis l'extérieur** du conteneur dans la CI (smoke test `docker run` + `curl`) ; ne pas reprendre une valeur imposée sans la relire.
