#!/bin/bash
# Controllo del registro e test con tutta la copia di lavoro (montata al posto del codice dell'immagine).
# pytest non e' nell'immagine: si installa al volo in una cartella temporanea (serve la rete solo per pip).
# Con PGPROVA=1 i test del database girano su un Postgres temporaneo (vedi db_prova.sh).
EXTRA=""
if [ "$PGPROVA" = "1" ]; then EXTRA="--network bandiprova -e PGHOST=pgprova -e PGUSER=postgres -e PGPASSWORD=prova -e PGDATABASE=prova"; fi
sudo docker run --rm ${EXTRA:---network bridge} -v /home/ubuntu/bandi-radar:/srv/app:ro \
  bandi-radar-raccolta sh -c "python -m app.fonti.verifica --solo-controllo 2>&1 | tail -5; pip install -q --target /tmp/pt pytest anthropic >/dev/null 2>&1; PYTHONPATH=/tmp/pt python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -15"
