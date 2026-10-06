"""Controllo delle schede senza IA (06/10/2026, richiesta di Matteo dopo il bando 423).

Ogni ora il regista ricontrolla le schede nuove o cambiate dall'ultimo controllo e salva in bandi.controllo:
- gravi: la scheda puo' ingannare il cliente (documenti di un altro bando, pagina condivisa con un doppione, date
  impossibili, contributo oltre la dotazione, "bando ufficiale" senza il testo del bando). Finche' ci sono, la scheda
  non si propone alle imprese (catalogo.proponibile);
- da_migliorare: manca un'informazione utile (vincolo senza spiegazione, fornitori non noti, fasi senza linee...).
Tutte compaiono in "Da rivedere" (pagina Lavorazione), da sistemare con gli strumenti di sessione o a mano.
Niente IA, niente rete: solo i dati gia' nel database. A mano: python -m app.schede.controlli [--tutti] [--bando ID]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone

from app.schede import ia

_FASI = re.compile(r"\b(fase|fasi|step)\s+(1|2|i|ii|uno|due)\b|\bin (due|tre|piu') fasi\b|\bprima fase\b|\bseconda fase\b",
                   re.IGNORECASE)
_RISERVA = re.compile(r"\b(riserv\w+|quota|ripartit\w+)\b[^.]{0,80}\b(dotazione|risorse|fondi|stanziamento)\b|"
                      r"\b(dotazione|risorse|stanziamento)\b[^.]{0,80}\b(riserv\w+|ripartit\w+|suddivis\w+)\b", re.IGNORECASE)


def problemi(b: dict, altri_sulla_pagina: list[dict], categorie_documenti: list[str]) -> tuple[list[str], list[str]]:
    """(gravi, da_migliorare) di una scheda. `b` e' la riga di bandi; `altri_sulla_pagina` i bandi non uniti con la stessa
    pagina ufficiale; `categorie_documenti` le categorie dei documenti del bando."""
    gravi, migliorare = [], []
    risposta = (b.get("dati") or {}).get("risposta") or {}
    if b.get("completezza") == "bando_ufficiale" and "bando" not in categorie_documenti and "decreto" not in categorie_documenti:
        if b.get("documentazione") == "bando":   # il filtro ha trovato il testo nella pagina o in un documento senza nome chiaro
            migliorare.append("il testo del bando c'e' ma non e' riconoscibile dal nome tra i documenti")
        else:
            gravi.append("scheda segnata 'bando ufficiale' ma tra i documenti non c'e' il testo del bando")
    for a in altri_sulla_pagina:
        if (a.get("titolo") or "").strip().lower() == (b.get("titolo") or "").strip().lower():
            gravi.append(f"possibile doppione: stessa pagina e stesso titolo del bando {a['id']}")
    if altri_sulla_pagina:
        migliorare.append(f"pagina ufficiale condivisa con {len(altri_sulla_pagina)} altri bandi (pagina elenco o doppioni): "
                          f"controllare i documenti ({', '.join(str(a['id']) for a in altri_sulla_pagina[:5])})")
    if b.get("data_apertura") and b.get("scadenza") and b["data_apertura"] > b["scadenza"]:
        gravi.append(f"apertura ({b['data_apertura']:%d/%m/%Y}) dopo la scadenza ({b['scadenza']:%d/%m/%Y})")
    if b.get("contributo_massimo") and b.get("dotazione") and float(b["contributo_massimo"]) > float(b["dotazione"]):
        gravi.append("contributo massimo per impresa piu' alto della dotazione dell'intero bando")
    if b.get("percentuale") is not None and not 0 <= float(b["percentuale"]) <= 100:
        gravi.append(f"percentuale fuori scala: {b['percentuale']}")
    # Quello che i controlli della scheda gia' dicono (vincoli senza dati e senza nota, fonti mancanti...).
    for p in ia.verifica_scheda(risposta) if risposta else []:
        if "vincolo" in p:
            migliorare.append(p)
    fornitore = ((b.get("vincoli_spese") or {}) if isinstance(b.get("vincoli_spese"), dict) else {}).get("fornitore") or {}
    if b.get("completezza") == "bando_ufficiale" and fornitore.get("stato") in (None, "non_noto"):
        migliorare.append("requisiti dei fornitori non noti (regola 21f): rileggere il bando")
    testo = " ".join(str(risposta.get(k) or "") for k in ("sintesi", "requisiti", "cosa_finanzia", "spese_ammesse"))
    if (_FASI.search(testo) or _RISERVA.search(testo)) and not (risposta.get("linee") or []):
        migliorare.append("il bando sembra a fasi o con la dotazione ripartita, ma la scheda non ha le linee (regola 21d)")
    return gravi, migliorare


def controlla(conn, limite: int = 500, tutti: bool = False, bando_id: int | None = None) -> dict:
    """Controlla le schede nuove o cambiate dall'ultimo controllo (o tutte). Ritorna i conteggi."""
    with conn.cursor() as cur:
        if bando_id:
            cur.execute("SELECT * FROM bandi WHERE id = %s", (bando_id,))
        else:
            cur.execute(f"""SELECT * FROM bandi WHERE dati IS NOT NULL AND unito_a IS NULL
                            {'' if tutti else "AND (controllo IS NULL OR (controllo->>'fatto_il')::timestamptz < aggiornato_il)"}
                            ORDER BY id LIMIT %s""", (limite,))
        bandi = [dict(r) for r in cur.fetchall()]
    conti = {"controllati": 0, "con_gravi": 0, "da_migliorare": 0}
    for b in bandi:
        with conn.cursor() as cur:
            cur.execute("SELECT id, titolo FROM bandi WHERE url = %s AND id <> %s AND unito_a IS NULL",
                        (b.get("url"), b["id"]))
            altri = [dict(r) for r in cur.fetchall()] if b.get("url") else []
            cur.execute("SELECT DISTINCT coalesce(categoria, tipo) AS c FROM allegati WHERE bando_id = %s AND annuncio_id IS NULL",
                        (b["id"],))
            categorie = [r["c"] for r in cur.fetchall()]
            gravi, migliorare = problemi(b, altri, categorie)
            cur.execute("UPDATE bandi SET controllo = %s WHERE id = %s",
                        (json.dumps({"fatto_il": datetime.now(timezone.utc).isoformat(), "gravi": gravi,
                                     "da_migliorare": migliorare}), b["id"]))
        conti["controllati"] += 1
        conti["con_gravi"] += bool(gravi)
        conti["da_migliorare"] += bool(migliorare)
    conn.commit()
    return conti


def da_rivedere(conn) -> list[dict]:
    """Le schede con problemi, prima quelle gravi e proponibili aperte (le vedrebbero i clienti)."""
    with conn.cursor() as cur:
        cur.execute("""SELECT id, titolo, ente, stato, scadenza, completezza, controllo
                       FROM bandi WHERE unito_a IS NULL AND controllo IS NOT NULL
                         AND (jsonb_array_length(controllo->'gravi') > 0 OR jsonb_array_length(controllo->'da_migliorare') > 0)
                       ORDER BY jsonb_array_length(controllo->'gravi') DESC,
                                (completezza = 'bando_ufficiale' AND stato IN ('aperto', 'in_arrivo')) DESC, scadenza NULLS LAST
                       LIMIT 500""")
        return [dict(r) for r in cur.fetchall()]


def main(argv: list[str] | None = None) -> int:
    from app.db.connessione import connetti

    p = argparse.ArgumentParser(description="Controllo delle schede senza IA")
    p.add_argument("--tutti", action="store_true")
    p.add_argument("--bando", type=int)
    args = p.parse_args(argv)
    with connetti() as conn:
        print(controlla(conn, limite=100000 if args.tutti else 500, tutti=args.tutti, bando_id=args.bando))
    return 0


if __name__ == "__main__":
    sys.exit(main())
