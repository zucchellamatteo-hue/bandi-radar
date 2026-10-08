"""Salva nel database gli esiti della verifica IA in sessione (secondo controllo, ISTRUZIONI_VERIFICA_IA.md): per ogni
/out/verifica/<cartella>/<id>/verifica_ia.json scrive bandi.secondo_controllo e, se la verifica li ha (dal 08/10),
bandi.tipo_procedura e bandi.verifica_documento (procedura nuova del regista, app/catena/procedura.py).

Uso: importa_verifica.py [--corrette] [--solo-documento] [--prova] CARTELLA [CARTELLA ...]
  --corrette        gli errori gravi di queste cartelle sono gia' stati corretti (applica_verifica.py o SQL a mano)
  --solo-documento  file documento.json (ISTRUZIONI_DOCUMENTO.md): solo tipo di agevolazione e verifica del
                    documento, il secondo controllo gia' salvato non si tocca
La data del controllo e' quella del file. Un controllo piu' vecchio di quello gia' salvato non lo sostituisce."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.db.connessione import connetti

TIPI = {"misura_di_legge", "sportello", "bando"}
PROBLEMI = {"manca", "solo_sintesi", "altro_bando", "edizione_vecchia", "bozza", "atto_generico", "graduatoria"}


def leggi(percorso: Path, cartella: str, corrette: bool) -> dict:
    d = json.loads(percorso.read_text())
    fatto_il = datetime.fromtimestamp(percorso.stat().st_mtime, timezone.utc).isoformat()
    problemi = d.get("problemi") or []
    gravi = sum(1 for p in problemi if p.get("gravita") == "grave")
    # Un problema grave rende grave l'esito, anche se l'agente ha scritto "da_correggere" (08/10: 1598, 3626, 1290).
    esito = "grave" if gravi else d.get("esito") if d.get("esito") in ("corretta", "da_correggere") else "da_correggere"
    r = {"id": int(percorso.parent.name),
         "secondo_controllo": {"esito": esito, "gravi": gravi, "minori": len(problemi) - gravi,
                               "correzioni_applicate": bool(corrette and gravi), "fatto_il": fatto_il, "da": "sessione",
                               "cartella": cartella, "note": (d.get("note") or "")[:500]},
         "tipo_procedura": d.get("tipo_procedura") if d.get("tipo_procedura") in TIPI else None, "verifica_documento": None}
    doc = d.get("documento") or {}
    if doc.get("verificato") in ("si", "no"):
        r["verifica_documento"] = {"verificato": doc["verificato"], "nome": (doc.get("nome") or "")[:300] or None,
                                   "problema": doc.get("problema") if doc.get("problema") in PROBLEMI else
                                   (None if doc["verificato"] == "si" else "manca"),
                                   "motivo": (doc.get("motivo") or "")[:500] or None,
                                   "deciso_da": "sessione", "deciso_il": fatto_il}
    return r


def solo_documento(cartelle: list[str], prova: bool) -> int:
    righe = [leggi(p, c, False) for c in cartelle
             for p in sorted(Path("/out/verifica", c).glob("*/documento.json")) if p.parent.name.isdigit()]
    salvati = 0
    with connetti() as conn, conn.cursor() as cur:
        for r in righe:
            if not r["verifica_documento"]:
                continue
            cur.execute("""UPDATE bandi SET tipo_procedura = coalesce(%s, tipo_procedura), verifica_documento = %s::jsonb
                           WHERE id = %s AND coalesce(verifica_documento->>'deciso_da', '') <> 'matteo'""",
                        (r["tipo_procedura"], json.dumps(r["verifica_documento"]), r["id"]))
            salvati += cur.rowcount
        conn.rollback() if prova else conn.commit()
    no = sum(1 for r in righe if (r["verifica_documento"] or {}).get("verificato") == "no")
    print(("PROVA: " if prova else "") + f"{len(righe)} verifiche del documento lette ({no} con il documento non valido), "
          f"{salvati} salvate")
    return 0


def main() -> int:
    argomenti = sys.argv[1:]
    corrette, prova = "--corrette" in argomenti, "--prova" in argomenti
    cartelle = [a for a in argomenti if not a.startswith("--")]
    if "--solo-documento" in argomenti:
        return solo_documento(cartelle, prova)
    righe = [leggi(p, c, corrette) for c in cartelle
             for p in sorted(Path("/out/verifica", c).glob("*/verifica_ia.json")) if p.parent.name.isdigit()]
    salvati = 0
    with connetti() as conn, conn.cursor() as cur:
        for r in righe:
            cur.execute("""UPDATE bandi SET secondo_controllo = %s::jsonb,
                                  tipo_procedura = coalesce(%s, tipo_procedura),
                                  verifica_documento = coalesce(%s::jsonb, verifica_documento)
                           WHERE id = %s AND (secondo_controllo IS NULL
                                 OR (secondo_controllo->>'fatto_il')::timestamptz <= %s::timestamptz)""",
                        (json.dumps(r["secondo_controllo"]), r["tipo_procedura"],
                         json.dumps(r["verifica_documento"]) if r["verifica_documento"] else None, r["id"],
                         r["secondo_controllo"]["fatto_il"]))
            salvati += cur.rowcount
        if prova:
            conn.rollback()
        else:
            conn.commit()
    gravi = sum(1 for r in righe if r["secondo_controllo"]["esito"] == "grave")
    print(("PROVA: " if prova else "") + f"{len(righe)} verifiche lette ({gravi} con errori gravi), {salvati} salvate; "
          f"{sum(1 for r in righe if r['verifica_documento'])} con la verifica del documento")
    return 0


if __name__ == "__main__":
    sys.exit(main())
