#!/bin/bash
# Come ar.sh, ma con il codice della COPIA DI LAVORO (~/bandi-radar/app): uno script di /tmp/claude-1000/ar sul DB di produzione.
leggi() { sudo grep "^$1=" /srv/bandi-radar/.env | head -n 1 | cut -d= -f2- | tr -d '"'; }
PGU=$(leggi POSTGRES_USER); PGD=$(leggi POSTGRES_DB)
sudo docker run --rm --network bandi-radar_default \
  -e PGHOST=db -e PGUSER="${PGU:-postgres}" -e PGDATABASE="${PGD:-bandi_radar}" -e PGPASSWORD="$(leggi POSTGRES_PASSWORD)" \
  -e PYTHONPATH=/srv/app -e ALLEGATI_CARTELLA=/srv/allegati -v bandi-radar_allegati:/srv/allegati:ro \
  -v /home/ubuntu/bandi-radar/app:/srv/app/app:ro -v /tmp/claude-1000/ar:/out \
  bandi-radar-raccolta python /out/"$@"
sudo chown -R ubuntu:ubuntu /tmp/claude-1000/ar
chmod -R a+rwX /tmp/claude-1000/ar
