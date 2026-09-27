#!/bin/bash
# Lancia uno script di /tmp/claude-1000/sp/schede nel servizio raccolta di produzione (codice di produzione,
# database di produzione), con la cartella montata in /out. Uso: schede.sh esporta.py | schede.sh importa.py [--prova]
cd /srv/bandi-radar || exit 1
chmod -R a+rwX /tmp/claude-1000/sp/schede
sudo -u deploy docker compose run --rm -T -e PYTHONPATH=/srv/app -v /tmp/claude-1000/sp/schede:/out raccolta python /out/"$@" 2>&1 \
  | grep -v -E "^ *(Container|Network) "
