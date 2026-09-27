#!/bin/bash
# Lancia un modulo Python nel servizio raccolta di produzione: prod.sh app.schede.bandi --prova
cd /srv/bandi-radar || exit 1
sudo -u deploy docker compose run --rm -T raccolta python -m "$@" 2>&1 | grep -v -E "^ *(Container|Network) "
