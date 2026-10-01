#!/bin/bash
# Lancia uno script Python con il CODICE DELLA COPIA DI LAVORO (~/bandi-radar/app) sul database di produzione.
# Uso: copia.sh /tmp/claude-1000/qualcosa.py   (lo script e' montato in /out)
leggi() { sudo grep "^$1=" /srv/bandi-radar/.env | head -n 1 | cut -d= -f2- | tr -d '"'; }
PGU=$(leggi POSTGRES_USER); PGD=$(leggi POSTGRES_DB)
sudo docker run --rm --network bandi-radar_default \
  -e PGHOST=db -e PGUSER="${PGU:-postgres}" -e PGDATABASE="${PGD:-bandi_radar}" -e PGPASSWORD="$(leggi POSTGRES_PASSWORD)" \
  -e PYTHONPATH=/srv/app -v /home/ubuntu/bandi-radar/app:/srv/app/app:ro -v /tmp/claude-1000/cp:/out bandi-radar-raccolta \
  python "/out/$(basename "$1")" "${@:2}"
