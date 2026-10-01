#!/bin/bash
# Compila la plancia (controllo dei tipi + build) in un contenitore Node usa e getta, dalla copia di lavoro.
sudo rm -rf /tmp/claude-1000/pb
mkdir -p /tmp/claude-1000/pb
cp -r /home/ubuntu/bandi-radar/plancia/. /tmp/claude-1000/pb/
rm -rf /tmp/claude-1000/pb/node_modules /tmp/claude-1000/pb/dist
sudo docker run --rm -v /tmp/claude-1000/pb:/p -w /p node:22-alpine sh -c "npm ci --silent >/dev/null 2>&1; npm run build 2>&1 | tail -n 40"
