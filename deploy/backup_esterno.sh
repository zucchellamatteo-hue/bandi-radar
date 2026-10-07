#!/bin/bash
# Backup esterno (dal 07/10/2026, decisione di Matteo): copia ogni notte il dump del database e i documenti scaricati
# su OVH Object Storage a Strasburgo (S3), lontano dal server di Gravelines.
#  - database: /var/backups/bandi-radar/db-AAAA-MM-GG.sql.gz (fatto alle 3:30 dal cron di bootstrap.sh) in db/,
#    si tengono 30 giorni;
#  - documenti (volume bandi-radar_allegati) in allegati/: si caricano solo i file nuovi o cambiati, niente si cancella.
# Le chiavi sono nel .env (BACKUP_S3_*), mai nel repository. L'esito finisce nella tabella esecuzioni (sistema
# "backup_esterno") e si vede nella pagina Supervisione. Lo lancia root dal cron /etc/cron.d/bandi-radar-backup-esterno.
# Uso: backup_esterno.sh [--solo-db]
set -uo pipefail
cd /srv/bandi-radar || exit 1
set -a
# shellcheck disable=SC1090
source <(grep -E '^BACKUP_S3_[A-Z]+=' .env)
set +a
DUMP=/var/backups/bandi-radar/db-$(date +%F).sql.gz
VOLUME=/var/lib/docker/volumes/bandi-radar_allegati/_data

# Il nome del database: quello del .env (POSTGRES_DB), altrimenti bandi_radar.
DB=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2-); DB=${DB:-bandi_radar}
sql() { docker compose exec -T db psql -U postgres -d "$DB" -qtAc "$1" 2>/dev/null; }

id=$(sql "INSERT INTO esecuzioni (sistema) VALUES ('backup_esterno') RETURNING id")
fine() {   # $1 = ok | errore, $2 = testo
  testo=${2//\'/\'\'}
  if [ "$1" = ok ]; then
    sql "UPDATE esecuzioni SET finito_il = now(), esito = 'ok', riepilogo = '$testo' WHERE id = ${id:-0}"
  else
    sql "UPDATE esecuzioni SET finito_il = now(), esito = 'errore', errore = '$testo' WHERE id = ${id:-0}"
  fi
  echo "$1: $2"
}

rclone() {
  docker run --rm --network host \
    -e RCLONE_CONFIG_OVH_TYPE=s3 -e RCLONE_CONFIG_OVH_PROVIDER=Other \
    -e RCLONE_CONFIG_OVH_ENDPOINT="$BACKUP_S3_ENDPOINT" -e RCLONE_CONFIG_OVH_REGION="$BACKUP_S3_REGIONE" \
    -e RCLONE_CONFIG_OVH_ACCESS_KEY_ID="$BACKUP_S3_CHIAVE" -e RCLONE_CONFIG_OVH_SECRET_ACCESS_KEY="$BACKUP_S3_SEGRETO" \
    -e RCLONE_CONFIG_OVH_NO_CHECK_BUCKET=true \
    -v /var/backups/bandi-radar:/db:ro -v "$VOLUME":/allegati:ro \
    rclone/rclone:1.68 "$@"
}

[ -s "$DUMP" ] || { fine errore "manca il dump di stanotte $DUMP"; exit 1; }
if ! uscita=$(rclone copy "/db/$(basename "$DUMP")" "ovh:$BACKUP_S3_CONTENITORE/db/" 2>&1); then
  fine errore "copia del database non riuscita: ${uscita: -300}"; exit 1
fi
rclone delete --min-age 30d "ovh:$BACKUP_S3_CONTENITORE/db/" >/dev/null 2>&1
riepilogo="database $(basename "$DUMP") ($(du -h "$DUMP" | cut -f1))"
if [ "${1:-}" != "--solo-db" ]; then
  if ! uscita=$(rclone copy /allegati "ovh:$BACKUP_S3_CONTENITORE/allegati/" --transfers 4 --stats-one-line --stats 0 -v 2>&1); then
    fine errore "$riepilogo copiato; documenti non riusciti: ${uscita: -300}"; exit 1
  fi
  nuovi=$(echo "$uscita" | grep -c "Copied (new)\|Copied (replaced")
  riepilogo="$riepilogo; documenti: $nuovi file nuovi o cambiati"
fi
copie=$(rclone lsf "ovh:$BACKUP_S3_CONTENITORE/db/" 2>/dev/null | wc -l)
fine ok "$riepilogo; copie del database fuori dal server: $copie"
