#!/bin/bash
# Lancia uno script di /tmp/claude-1000/ar nel servizio raccolta di produzione (codice e database di produzione),
# con la cartella montata in /out. Uso: ar.sh esporta.py | ar.sh importa.py [--prova]
cd /srv/bandi-radar || exit 1
sudo -u deploy docker compose run --rm -T -e PYTHONPATH=/srv/app -v /tmp/claude-1000/ar:/out raccolta python /out/"$@" 2>&1 \
  | grep -v -E "^ *(Container|Network) "
sudo chown -R ubuntu:ubuntu /tmp/claude-1000/ar
chmod -R a+rwX /tmp/claude-1000/ar
