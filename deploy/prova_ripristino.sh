#!/bin/bash
# Prova di ripristino del backup esterno: scarica da OVH Object Storage l'ultima copia del database, la carica in un
# Postgres temporaneo (container usa e getta, senza toccare la produzione) e conta bandi, annunci e fonti.
# Uso (root): deploy/prova_ripristino.sh
set -uo pipefail
cd /srv/bandi-radar || exit 1
set -a
# shellcheck disable=SC1090
source <(grep -E '^BACKUP_S3_[A-Z]+=' .env)
set +a
LAVORO=$(mktemp -d)
trap 'docker rm -f pgripristino >/dev/null 2>&1; rm -rf "$LAVORO"' EXIT
rclone() {
  docker run --rm --network host \
    -e RCLONE_CONFIG_OVH_TYPE=s3 -e RCLONE_CONFIG_OVH_PROVIDER=Other \
    -e RCLONE_CONFIG_OVH_ENDPOINT="$BACKUP_S3_ENDPOINT" -e RCLONE_CONFIG_OVH_REGION="$BACKUP_S3_REGIONE" \
    -e RCLONE_CONFIG_OVH_ACCESS_KEY_ID="$BACKUP_S3_CHIAVE" -e RCLONE_CONFIG_OVH_SECRET_ACCESS_KEY="$BACKUP_S3_SEGRETO" \
    -e RCLONE_CONFIG_OVH_NO_CHECK_BUCKET=true -v "$LAVORO":/lavoro rclone/rclone:1.68 "$@"
}
ultima=$(rclone lsf "ovh:$BACKUP_S3_CONTENITORE/db/" | sort | tail -1)
[ -n "$ultima" ] || { echo "nessuna copia del database nello spazio esterno"; exit 1; }
echo "ultima copia: $ultima"
rclone copy "ovh:$BACKUP_S3_CONTENITORE/db/$ultima" /lavoro/ || exit 1
docker run -d --name pgripristino -e POSTGRES_PASSWORD=prova postgres:16-alpine >/dev/null
for i in $(seq 1 30); do docker exec pgripristino pg_isready -U postgres >/dev/null 2>&1 && break; sleep 1; done
sleep 2
gunzip -c "$LAVORO/$ultima" | docker exec -i pgripristino psql -U postgres -q -o /dev/null 2>&1 | grep -v "already exists" | tail -3
DB=$(grep -E '^POSTGRES_DB=' .env | cut -d= -f2-); DB=${DB:-bandi_radar}
docker exec pgripristino psql -U postgres -d "$DB" -tAc \
  "SELECT 'bandi: ' || (SELECT count(*) FROM bandi) || ', annunci: ' || (SELECT count(*) FROM annunci) || ', fonti: ' || (SELECT count(*) FROM fonti) || ', ultimo annuncio: ' || (SELECT max(trovato_il)::date FROM annunci)"
