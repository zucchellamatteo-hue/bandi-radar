#!/bin/bash
# Query sul database di produzione: sql.sh "SELECT ..."  oppure  sql.sh -f file.sql
cd /srv/bandi-radar || exit 1
if [ "$1" = "-f" ]; then
  sudo -u deploy docker compose exec -T db psql -U postgres bandi_radar -P pager=off < "$2"
else
  sudo -u deploy docker compose exec -T db psql -U postgres bandi_radar -P pager=off -c "$1"
fi
