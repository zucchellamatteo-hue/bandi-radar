#!/bin/bash
# Reinstalla gli strumenti delle sessioni da strumenti/sessione/ (dopo un riavvio /tmp si svuota).
cd /home/ubuntu/bandi-radar || exit 1
git checkout -q main
git pull -q origin main
mkdir -p /tmp/claude-1000/ar/fascicoli /tmp/claude-1000/fd /tmp/claude-1000/cp
cp strumenti/sessione/ar/* /tmp/claude-1000/ar/
cp strumenti/sessione/sh/*.sh /tmp/claude-1000/
cp strumenti/sessione/sh/controlli.sh /tmp/claude-1000/fd/
cp strumenti/sessione/sh/foto.py /tmp/claude-1000/cp/
chmod +x /tmp/claude-1000/*.sh /tmp/claude-1000/fd/*.sh
chmod 755 /tmp/claude-1000/cp
touch /tmp/claude-1000/ar/prenotati.txt /tmp/claude-1000/ar/prenotati_s.txt
chmod -R a+rwX /tmp/claude-1000/ar
git log --oneline -1
ls /tmp/claude-1000
