#!/bin/bash
# Aspetta (al massimo 20 minuti) che la produzione abbia la migrazione indicata. Uso: aspetta_deploy.sh 013_esecuzioni.sql
for i in $(seq 1 40); do
  if /tmp/claude-1000/sql.sh "SELECT nome FROM schema_migrazioni WHERE nome = '$1'" | grep -q "$1"; then
    echo "in produzione dopo $((i * 30)) secondi"
    sudo git -C /srv/bandi-radar log --oneline -1
    exit 0
  fi
  sleep 30
done
echo "non ancora in produzione dopo 20 minuti"
