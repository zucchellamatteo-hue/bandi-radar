#!/bin/bash
# Costruisce l'immagine della raccolta dalla copia di lavoro (con l'OCR) e lancia un modulo sul database e
# sugli allegati di produzione. Uso: ocr_prova.sh app.schede.allegati --rileggi-illeggibili --prova [--bando N]
cd /home/ubuntu/bandi-radar || exit 1
sudo docker build -q -f deploy/Dockerfile.raccolta -t bandi-radar-raccolta-ocr . >/dev/null || exit 1
leggi() { sudo grep "^$1=" /srv/bandi-radar/.env | head -n 1 | cut -d= -f2- | tr -d '"'; }
PGU=$(leggi POSTGRES_USER); PGD=$(leggi POSTGRES_DB)
sudo docker run --rm --network bandi-radar_default \
  -e PGHOST=db -e PGUSER="${PGU:-postgres}" -e PGDATABASE="${PGD:-bandi_radar}" -e PGPASSWORD="$(leggi POSTGRES_PASSWORD)" \
  -e ALLEGATI_CARTELLA=/srv/allegati -v bandi-radar_allegati:/srv/allegati${RW:-:ro} bandi-radar-raccolta-ocr \
  python -m "$@"
