"""Servizio di raccolta: ogni ora controlla le fonti in scadenza. Gira come container 'raccolta' in Docker Compose."""

from __future__ import annotations

import os
import sys
import time
import traceback

from app.raccolta.esegui import esegui

INTERVALLO_SECONDI = int(os.environ.get("RACCOLTA_INTERVALLO_SECONDI", "3600"))


def main() -> int:
    print(f"Raccolta avviata: controllo delle fonti in scadenza ogni {INTERVALLO_SECONDI} secondi.", flush=True)
    while True:
        try:
            esegui()
        except Exception:  # noqa: BLE001 - il servizio non deve morire per un errore di un giro
            traceback.print_exc()
        time.sleep(INTERVALLO_SECONDI)


if __name__ == "__main__":
    sys.exit(main())
