#!/bin/bash
# Plancia di prova dalla copia di lavoro, sul database di produzione, SENZA migrazioni, su 127.0.0.1:8090.
# Uso: app_prova.sh su | giu
if [ "$1" = "giu" ]; then sudo docker rm -f br-prova >/dev/null 2>&1; echo "fermata"; exit 0; fi
cd /home/ubuntu/bandi-radar || exit 1
sudo docker build -q -t bandi-radar-app-prova . >/dev/null || exit 1
leggi() { sudo grep "^$1=" /srv/bandi-radar/.env | head -n 1 | cut -d= -f2- | tr -d '"'; }
PGU=$(leggi POSTGRES_USER); PGD=$(leggi POSTGRES_DB)
sudo docker rm -f br-prova >/dev/null 2>&1
sudo docker run -d --name br-prova --network bandi-radar_default -p 127.0.0.1:8090:8000 \
  -e PGHOST=db -e PGUSER="${PGU:-postgres}" -e PGDATABASE="${PGD:-bandi_radar}" -e PGPASSWORD="$(leggi POSTGRES_PASSWORD)" \
  -e BASIC_AUTH_USER=prova -e BASIC_AUTH_PASSWORD=prova -e ALLEGATI_CARTELLA=/srv/allegati \
  -v bandi-radar_allegati:/srv/allegati:ro bandi-radar-app-prova uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null
sleep 4
curl -s -u prova:prova -o /dev/null -w "health %{http_code}\n" http://127.0.0.1:8090/health
