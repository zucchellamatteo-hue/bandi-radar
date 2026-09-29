#!/bin/bash
# Test completi (anche quelli sul database) su un Postgres di prova VUOTO, poi lo rimuove.
sudo docker network create bandiprova >/dev/null 2>&1 || true
sudo docker rm -f pgprova >/dev/null 2>&1 || true
sudo docker run -d --name pgprova --network bandiprova -e POSTGRES_PASSWORD=prova -e POSTGRES_DB=prova postgres:16-alpine >/dev/null
for i in $(seq 1 30); do sudo docker exec pgprova pg_isready -U postgres -d prova >/dev/null 2>&1 && break; sleep 1; done
sleep 2
PGPROVA=1 /tmp/claude-1000/fd/controlli.sh
sudo docker rm -f pgprova >/dev/null 2>&1
sudo docker network rm bandiprova >/dev/null 2>&1
echo "postgres di prova rimosso"
