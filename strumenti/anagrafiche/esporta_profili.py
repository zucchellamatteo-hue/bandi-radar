"""Profili ANONIMI delle imprese prospect per le campagne di bandinQiaro (05/10/2026).

Gira sul computer di Matteo, accanto al database `leadgen` (docs/ricerche/2026-09-25_schema_anagrafiche_leadgen.md).
A bandinQiaro va solo il file profili_anonimi.json: per ogni impresa un codice casuale e i dati che servono
all'abbinamento (forma giuridica, provincia, ATECO, dimensione stimata, dipendenti, fatturato). Nomi, P.IVA,
email, telefoni, indirizzi, soci restano qui: la corrispondenza codice -> P.IVA va in corrispondenze.csv, che NON
si manda a nessuno e serve per completare a casa le lettere preparate da bandinQiaro.

Uso (nella cartella del progetto lead-generation, con il suo ambiente Python che ha gia' psycopg):
    python esporta_profili.py --env C:\\Users\\matte\\lead-generation\\.env --uscita C:\\Users\\matte\\bandi_radar_export
Poi carica profili_anonimi.json nella pagina Campagne di bandinQiaro.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import re
import secrets
import sys
from pathlib import Path

import psycopg

# Suffissi della ragione sociale -> forma giuridica di bandinQiaro (app/schede/campi.py).
FORME = [
    (r"\bS\.?\s?R\.?\s?L\.?\s?S\.?\b|SEMPLIFICATA", "srls"),
    (r"\bS\.?\s?R\.?\s?L\.?\b|RESPONSABILITA'? LIMITATA", "srl"),
    (r"\bS\.?\s?P\.?\s?A\.?\b|PER AZIONI", "spa"),
    (r"\bS\.?\s?A\.?\s?P\.?\s?A\.?\b", "sapa"),
    (r"\bS\.?\s?N\.?\s?C\.?\b|NOME COLLETTIVO", "snc"),
    (r"\bS\.?\s?A\.?\s?S\.?\b|ACCOMANDITA SEMPLICE", "sas"),
    (r"\bS\.?\s?S\.?\b|SOCIETA' SEMPLICE|SOCIETA SEMPLICE", "societa_semplice"),
    (r"COOPERATIVA|\bSOC\.?\s?COOP\b|\bS\.?\s?C\.?\b", "cooperativa"),
    (r"CONSORZIO|\bSCARL\b", "consorzio"),
]
_PROVINCIA = re.compile(r"\(([A-Z]{2})\)\s*$")


def leggi_env(percorso: Path) -> dict:
    valori = {}
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        if "=" in riga and not riga.lstrip().startswith("#"):
            k, v = riga.split("=", 1)
            valori[k.strip()] = v.strip().strip('"').strip("'")
    return valori


def forma_giuridica(denominazione: str | None) -> str | None:
    d = (denominazione or "").upper()
    for regola, forma in FORME:
        if re.search(regola, d):
            return forma
    return None   # spesso ditta individuale, ma senza certezza meglio "non indicata" ("da verificare" nei bandi)


def numero(testo) -> float | None:
    if testo is None:
        return None
    try:
        return float(str(testo).replace(".", "").replace(",", ".")) if "," in str(testo) else float(testo)
    except ValueError:
        return None


def dimensione(dipendenti: float | None, ricavi_euro: float | None) -> str | None:
    """Stima UE 2003/361 senza totale di bilancio: la classe piu' grande tra dipendenti e ricavi (prudente)."""
    classi = []
    if dipendenti is not None:
        classi.append(0 if dipendenti < 10 else 1 if dipendenti < 50 else 2 if dipendenti < 250 else 3)
    if ricavi_euro is not None:
        classi.append(0 if ricavi_euro <= 2e6 else 1 if ricavi_euro <= 10e6 else 2 if ricavi_euro <= 50e6 else 3)
    return ("micro", "piccola", "media", "grande")[max(classi)] if classi else None


def ateco(codice: str | None) -> str | None:
    cifre = re.sub(r"\D", "", codice or "")
    if len(cifre) < 2:
        return None
    parti = [cifre[0:2], cifre[2:4], cifre[4:6]]
    return ".".join(p for p in parti if p)


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--env", required=True, type=Path, help="file .env del progetto lead-generation")
    a.add_argument("--uscita", required=True, type=Path, help="cartella dove scrivere i file")
    a.add_argument("--solo-tier", default="", help="es. A,B: solo le imprese di queste fasce di leads_master")
    args = a.parse_args()
    env = leggi_env(args.env)
    args.uscita.mkdir(parents=True, exist_ok=True)
    # Il segreto rende il codice stabile tra un'esportazione e l'altra senza poter risalire alla P.IVA.
    file_segreto = args.uscita / "segreto_codici.txt"
    if not file_segreto.exists():
        file_segreto.write_text(secrets.token_hex(32))
    segreto = file_segreto.read_text().strip().encode()

    tier = [t.strip().upper() for t in args.solo_tier.split(",") if t.strip()]
    sql = """
        SELECT e.partita_iva, e.denominazione, e.ateco, e.dipendenti, e.fatturato, e.sede,
               (SELECT b.ricavi FROM leads_bilancio b WHERE b.partita_iva = e.partita_iva AND b.ricavi IS NOT NULL
                ORDER BY b.anno DESC LIMIT 1) AS ricavi,
               (SELECT m.provincia FROM leads_master m WHERE m.partita_iva = e.partita_iva LIMIT 1) AS provincia,
               (SELECT m.tier FROM leads_master m WHERE m.partita_iva = e.partita_iva LIMIT 1) AS tier
        FROM leads_enriched e
        WHERE e.esito = 'ok' AND coalesce(lower(e.stato), 'attiva') LIKE 'attiv%' AND e.partita_iva IS NOT NULL"""
    with psycopg.connect(host=env.get("DB_HOST", "localhost"), port=env.get("DB_PORT", "5432"),
                         dbname=env.get("DB_NAME", "leadgen"), user=env.get("DB_USER"), password=env.get("DB_PASSWORD")) as conn:
        righe = conn.execute(sql).fetchall()

    profili, corrispondenze, scartate = [], [], 0
    for piva, denominazione, cod_ateco, dip, fatt, sede, ricavi, provincia, t in righe:
        if tier and (t or "").upper() not in tier:
            continue
        provincia = provincia or (m.group(1) if (m := _PROVINCIA.search(sede or "")) else None)
        codice_ateco = ateco(cod_ateco)
        if not provincia or not codice_ateco:
            scartate += 1
            continue
        ricavi_euro = float(ricavi) * 1e6 if ricavi is not None else (numero(fatt) * 1e6 if numero(fatt) else None)
        dipendenti = numero(dip)
        codice = "p-" + hmac.new(segreto, piva.encode(), hashlib.sha256).hexdigest()[:12]
        profilo = {"soggetto": "impresa", "forma_giuridica": forma_giuridica(denominazione),
                   "sedi": [{"tipo": "legale_e_operativa", "provincia": provincia}], "ateco": [codice_ateco],
                   "dimensione": dimensione(dipendenti, ricavi_euro),
                   "dipendenti": int(dipendenti) if dipendenti is not None else None,
                   "fatturato": round(ricavi_euro) if ricavi_euro else None}
        profili.append({"codice": codice, "profilo": profilo})
        corrispondenze.append((codice, piva, denominazione))

    (args.uscita / "profili_anonimi.json").write_text(json.dumps({"profili": profili}, ensure_ascii=False))
    with (args.uscita / "corrispondenze.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codice", "partita_iva", "denominazione"])
        w.writerows(corrispondenze)
    print(f"Profili anonimi: {len(profili)} (scartate {scartate} senza provincia o ATECO).")
    print(f"Da caricare in bandinQiaro: {args.uscita / 'profili_anonimi.json'}")
    print(f"Da NON mandare a nessuno: {args.uscita / 'corrispondenze.csv'} e segreto_codici.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
