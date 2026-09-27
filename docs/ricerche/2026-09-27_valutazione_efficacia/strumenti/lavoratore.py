"""Un lavoratore della pagina ufficiale o degli allegati, per un gruppo di siti (26/09/2026).

  lavoratore.py pagina|allegati K N

Il lavoratore K di N si occupa solo dei siti con crc32(sito) % N == K: ogni sito e' sempre nelle mani di un solo
lavoratore, quindi riceve una richiesta alla volta con le pause di sempre (piu' 2 secondi tra un bando e l'altro).
Chiama le funzioni di produzione (app.schede.pagina_ufficiale.esegui, app.schede.allegati.esegui) un bando alla
volta. Ogni bando si prova una volta sola per giro: gli errori di rete si riprendono con i comandi normali.
"""

import sys
import time
import zlib
from urllib.parse import urlsplit

from app.db.connessione import connetti

modo, k, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
provati: set[int] = set()


def sito(url: str | None) -> str:
    s = urlsplit(url or "").netloc.lower()
    return s[4:] if s.startswith("www.") else s


def mio(url: str | None) -> bool:
    return zlib.crc32(sito(url).encode()) % n == k


def prossimo(conn) -> tuple[int | None, bool]:
    """(bando da fare, c'e' ancora lavoro altrove che potrebbe diventare mio)."""
    with conn.cursor() as cur:
        if modo == "pagina":
            cur.execute("""SELECT b.id, (SELECT a.url FROM annunci a WHERE a.bando_id = b.id ORDER BY a.id LIMIT 1) AS url
                           FROM bandi b WHERE b.pagina_stato IS NULL ORDER BY b.id""")
            righe = cur.fetchall()
            altro = False
        else:
            cur.execute("""SELECT id, url FROM bandi WHERE pagina_stato = 'trovata' AND url IS NOT NULL
                           AND allegati_cercati_il IS NULL ORDER BY id""")
            righe = cur.fetchall()
            cur.execute("SELECT count(*) AS c FROM bandi WHERE pagina_stato IS NULL")
            altro = cur.fetchone()["c"] > 0
    conn.commit()
    for r in righe:
        if r["id"] not in provati and mio(r["url"]):
            return r["id"], altro
    return None, altro


def main() -> int:
    if modo == "pagina":
        from app.schede.pagina_ufficiale import esegui
    else:
        from app.schede.allegati import esegui
    fatti = 0
    with connetti() as conn:
        while True:
            bando, altro = prossimo(conn)
            if bando is None:
                if altro:
                    time.sleep(60)
                    continue
                break
            provati.add(bando)
            try:
                esegui(bando_id=bando)
            except Exception as exc:   # un bando che rompe non ferma gli altri
                print(f"ERRORE [bando {bando}] {type(exc).__name__}: {str(exc)[:200]}", flush=True)
            fatti += 1
            time.sleep(2)
    print(f"=== lavoratore {modo} {k}/{n}: finito, {fatti} bandi ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
