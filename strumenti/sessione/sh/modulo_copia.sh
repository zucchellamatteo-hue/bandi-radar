#!/bin/bash
# Lancia un modulo (python -m ...) con codice E registro della copia di lavoro, sul database e gli allegati di produzione.
# Uso: modulo_copia.sh app.schede.pagina_ufficiale --bando 2311
leggi() { sudo grep "^$1=" /srv/bandi-radar/.env | head -n 1 | cut -d= -f2- | tr -d '"'; }
PGU=$(leggi POSTGRES_USER); PGD=$(leggi POSTGRES_DB)
sudo docker run --rm --network bandi-radar_default \
  -e PGHOST=db -e PGUSER="${PGU:-postgres}" -e PGDATABASE="${PGD:-bandi_radar}" -e PGPASSWORD="$(leggi POSTGRES_PASSWORD)" \
  -e ALLEGATI_CARTELLA=/srv/allegati -v bandi-radar_allegati:/srv/allegati \
  -v /home/ubuntu/bandi-radar/app:/srv/app/app:ro -v /home/ubuntu/bandi-radar/fonti:/srv/app/fonti:ro \
  bandi-radar-raccolta python -m "$@"
