"""Carica tra i documenti di un bando i file scaricati a mano (06/10/2026: siti con protezione anti-robot o documenti
in sottopagine che la ricerca automatica non segue, es. Green Tour). La cartella /out/manuali/<nome>/ contiene i file
e un elenco.md con la tabella | file | nome | categoria | url |; per i PDF si usa il testo nel .txt accanto, se c'e'.
I file vengono copiati in ALLEGATI_CARTELLA/b<id>/. Uso: carica_manuali.py ID_BANDO NOME_CARTELLA [--prova]"""
import hashlib
import re
import shutil
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import allegati


def righe(elenco: Path):
    for riga in elenco.read_text(encoding="utf-8").splitlines():
        celle = [c.strip() for c in riga.strip().strip("|").split("|")]
        if len(celle) < 4 or celle[0] in ("file", "---") or set(celle[0]) <= {"-"}:
            continue
        file = celle[0].split()[0]
        url = re.search(r"https?://\S+?(?=[\s)]|$)", celle[3])
        if "*" in file or not url:
            continue
        yield file, celle[1], celle[2], url.group(0)


def main() -> int:
    bando, nome = int(sys.argv[1]), sys.argv[2]
    prova = "--prova" in sys.argv
    sorgente = Path("/out/manuali") / nome
    destinazione = allegati.CARTELLA / f"b{bando}"
    risultati, categorie = [], {}
    for file, titolo, categoria, url in righe(sorgente / "elenco.md"):
        percorso = sorgente / file
        if not percorso.exists() or percorso.stat().st_size < 500:
            print("manca o vuoto, salto:", file)
            continue
        tipo = percorso.suffix.lstrip(".").lower() or "file"
        tipo = "pagina" if tipo in ("html", "htm") else tipo
        txt = percorso.with_suffix(".txt")
        testo = txt.read_text(encoding="utf-8") if txt.exists() and txt != percorso else allegati.estrai_testo(percorso, tipo)
        dati = percorso.read_bytes()
        locale = f"b{bando}/manuale_{percorso.name}"
        if not prova:
            destinazione.mkdir(parents=True, exist_ok=True)
            shutil.copy(percorso, allegati.CARTELLA / locale)
        risultati.append(allegati.Risultato(url, titolo[:200], tipo, len(dati), hashlib.sha256(dati).hexdigest(), locale,
                                            allegati._senza_nul(testo) if testo else None))
        categorie[url] = categoria
        print(f"{categoria:12} {tipo:5} {len(testo or ''):>8} car.  {titolo[:80]}")
    if prova:
        return 0
    with connetti() as conn:
        allegati.salva_bando(conn, bando, risultati)
        with conn.cursor() as cur:   # la categoria scelta da chi ha scaricato vale piu' di quella dedotta dal nome
            for url, categoria in categorie.items():
                cur.execute("UPDATE allegati SET categoria = %s WHERE bando_id = %s AND annuncio_id IS NULL AND url = %s",
                            (categoria, bando, url))
        conn.commit()
    print(f"caricati {len(risultati)} documenti nel bando {bando}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
