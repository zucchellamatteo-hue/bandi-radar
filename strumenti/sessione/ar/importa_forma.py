"""Importa /out/forma/<id>/forma.json (scritto dagli agenti) nella colonna forma_incentivo, con la stessa pulizia
e gli stessi controlli dell'API (ia.prepara_scheda, ia.verifica_forma_incentivo). Tocca solo quel blocco: il resto
della scheda resta com'e'. I problemi trovati si aggiungono a dati.problemi. Uso: importa_forma.py [--prova]"""
import json
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia

OUT = Path("/out/forma")


def main() -> int:
    prova = "--prova" in sys.argv
    importate = con_problemi = rotte = 0
    with connetti() as conn:
        for f in sorted(OUT.glob("*/forma.json")):
            bando_id = int(f.parent.name)
            if (f.parent / "importata").exists():
                continue
            try:
                grezza = json.loads(f.read_text())
            except json.JSONDecodeError as exc:
                print(f"[{bando_id}] forma.json non valido: {exc}")
                rotte += 1
                continue
            scheda, tolti = ia.prepara_scheda({"forma_incentivo": grezza})
            fi = scheda["forma_incentivo"]
            problemi = [t for t in tolti if t.startswith("forma_incentivo")] + ia.verifica_forma_incentivo(fi)
            if not fi.get("righe"):
                print(f"[{bando_id}] nessuna riga: non importata")
                rotte += 1
                continue
            con_problemi += bool(problemi)
            if prova:
                print(f"[{bando_id}] {len(fi['righe'])} righe; problemi: {problemi}")
                continue
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('bandi_radar.causa', %s, true)",
                            ("forma dell'incentivo compilata in sessione (Claude Code, senza API)",))
                cur.execute("""UPDATE bandi SET forma_incentivo = %s,
                                      dati = jsonb_set(coalesce(dati, '{}'::jsonb), '{problemi}',
                                                       coalesce(dati->'problemi', '[]'::jsonb) || %s::jsonb)
                               WHERE id = %s""", (json.dumps(fi), json.dumps(problemi), bando_id))
            conn.commit()
            (f.parent / "importata").write_text("")
            importate += 1
    print(f"importate {importate}, con problemi {con_problemi}, non valide {rotte}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
