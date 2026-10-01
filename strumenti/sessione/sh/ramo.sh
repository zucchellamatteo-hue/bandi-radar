#!/bin/bash
# Branch nuovo da main aggiornato. Uso: ramo.sh nome-branch
cd /home/ubuntu/bandi-radar || exit 1
git checkout -q main
git pull -q origin main
git checkout -q -b "$1"
git branch --show-current
git status --short
