#!/bin/bash
# Fotografa la plancia di prova (app_prova.sh su) con Chromium dell'immagine della raccolta. Foto in /tmp/claude-1000/cp.
chmod a+rwx /tmp/claude-1000/cp
chmod a+r /tmp/claude-1000/cp/*.py
sudo docker run --rm --network bandi-radar_default -v /tmp/claude-1000/cp:/out bandi-radar-raccolta python /out/${FOTO:-foto.py} "$@"
