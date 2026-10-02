#!/bin/bash
# Aspetta i controlli di GitHub su una PR e la unisce solo se sono tutti verdi. Uso: unisci_verde.sh NUMERO
cd /home/ubuntu/bandi-radar || exit 1
for i in $(seq 1 60); do
  esiti=$(gh pr checks "$1" 2>/dev/null | cut -f2 | sort -u | tr '\n' ' ')
  if [ "$esiti" = "pass " ]; then
    gh pr merge "$1" --merge 2>&1 | grep -v "Projects (classic)" | tail -n 1
    echo "PR $1: $(gh pr view "$1" --json state -q .state)"; exit 0
  fi
  case "$esiti" in *fail*) echo "PR $1: controlli FALLITI"; gh pr checks "$1"; exit 1 ;; esac
  sleep 20
done
echo "PR $1: controlli non finiti dopo 20 minuti ($esiti)"
