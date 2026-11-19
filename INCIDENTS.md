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

## Incident n°2 | Aucun pipeline sur `main` après la fusion, image jamais publiée
- **Partie / étape :** Partie 3 | 3.4 (vérifier qu'un pipeline tourne sur `main`)
- **Symptôme observé :** après la fusion de la PR `ci/pipeline`, l'onglet Actions ne montre que l'exécution liée à la PR (job `image` ignoré, ce qui est normal). Aucune exécution n'est déclenchée par le push sur `main`, et aucun paquet `tp-devops-aks` n'apparaît dans l'onglet Packages.
- **Diagnostic :**
  - Onglet Actions, filtre `branch:main` : aucune exécution.
  - `git branch -a` : seules `main` et `origin/main` existent, aucune branche `master`.
  - Relecture de `.github/workflows/ci-cd.yml` : `on.push.branches: [master]` alors que `on.pull_request.branches: [main]`.
- **Cause racine :** le modèle fourni par l'équipe filtre les push sur `master`, ancienne branche par défaut. GitHub nomme la branche par défaut `main` depuis 2020 : le déclencheur `push` ne correspond donc à aucune branche.
- **Correction appliquée :** `.github/workflows/ci-cd.yml`, `branches: [master]` remplacé par `branches: [main]` (branche `fix/ci-branche-main`, commit `fix(ci): déclencher le pipeline sur main`, PR fusionnée). Le push de fusion a déclenché le pipeline complet, image publiée avec les tags `sha-…` et `latest`.
- **Comment l'éviter à l'avenir :** vérifier les déclencheurs (`on:`) dès la relecture de la PR ; activer la règle de protection de `main` qui exige le statut « Qualité et tests » (bonus B1) ; passer `actionlint` sur les workflows.

## Incident n°3 | Pods en `OOMKilled` puis `CrashLoopBackOff`
- **Partie / étape :** Partie 4 | 4.2 (`kubectl apply` du Deployment)
- **Symptôme observé :** `kubectl get pods -w` affiche les pods en `0/1 Running`, puis `OOMKilled`, puis `CrashLoopBackOff` ; la colonne `RESTARTS` augmente sans cesse. Les pods ne passent jamais `1/1`.
- **Diagnostic :**
  - `kubectl describe pod <pod>` : `Last State: Terminated`, `Reason: OOMKilled`, `Exit Code: 137` (128 + 9, signal SIGKILL envoyé par le noyau) ; événements `Back-off restarting failed container`.
  - `kubectl logs <pod> --previous` : gunicorn démarre (`Booting worker with pid …`) puis le conteneur est tué, sans trace d'erreur Python : c'est bien une coupure externe.
  - Mesure de référence hors cluster : gunicorn (processus maître + 2 workers, Flask chargé) occupe environ **57 Mio** (somme des PSS des 3 processus), soit près du double de la limite imposée de **32Mi**.
- **Cause racine :** `limits.memory: 32Mi` est inférieur à l'empreinte mémoire réelle de l'application. Le cgroup du conteneur dépasse sa limite, le noyau déclenche l'OOM killer.
- **Correction appliquée :** `k8s/deployment.yaml`, `requests.memory` 16Mi → **64Mi** et `limits.memory` 32Mi → **128Mi** (marge x2 sur la mesure, CPU inchangé), justification écrite en commentaire dans le manifeste. Contrôle : `(2 replicas + 1 maxSurge) x 128Mi = 384Mi` reste dans le quota `limits.memory` du namespace (vérifié avec `kubectl describe resourcequota`). Commit `fix(k8s): ressources mémoire adaptées à gunicorn`, branche `feat/k8s`.
- **Comment l'éviter à l'avenir :** dimensionner `requests`/`limits` à partir d'une mesure (`docker stats`, `kubectl top pods`, bonus B5) et non d'une valeur arbitraire ; garder les ressources versionnées et justifiées dans le manifeste.
