"""Importa /out/complemento/<id>/complemento.json: forma dell'incentivo (come importa_forma.py), codici ATECO
ricavati dalla descrizione e regioni/province, solo dove la scheda li aveva vuoti, con avvertenza e fonte nella scheda.
Uso: importa_complemento.py [--prova]"""
import json
import re
import sys
from pathlib import Path

from app.db.connessione import connetti
from app.schede import campi, ia

OUT = Path("/out/complemento")
_ATECO = re.compile(r"^([A-U]|\d{2}(\.\d{1,2}){0,2})$")


def main() -> int:
    prova = "--prova" in sys.argv
    conti = {"forma": 0, "ateco": 0, "territorio": 0, "rotti": 0}
    with connetti() as conn:
        for f in sorted(OUT.glob("*/complemento.json"), key=lambda p: int(p.parent.name)):
            bid = int(f.parent.name)
            if (f.parent / "importato").exists():
                continue
            try:
                c = json.loads(f.read_text())
            except json.JSONDecodeError as exc:
                print(f"[{bid}] non valido: {exc}")
                conti["rotti"] += 1
                continue
            with conn.cursor() as cur:
                cur.execute("SELECT codici_ateco, territorio_regioni, territorio_province, forma_incentivo, dati FROM bandi WHERE id=%s", (bid,))
                b = cur.fetchone()
            modifiche, dati = {}, b["dati"] or {}
            avvertenze, problemi = list(dati.get("avvertenze") or []), list(dati.get("problemi") or [])
            fonti = dict(dati.get("fonti") or {})
            if isinstance(c.get("forma_incentivo"), dict) and not (b["forma_incentivo"] or {}).get("righe"):
                scheda, tolti = ia.prepara_scheda({"forma_incentivo": c["forma_incentivo"]})
                fi = scheda["forma_incentivo"]
                if fi.get("righe"):
                    modifiche["forma_incentivo"] = json.dumps(fi)
                    problemi += [t for t in tolti if t.startswith("forma_incentivo")] + ia.verifica_forma_incentivo(fi)
                    conti["forma"] += 1
            a = c.get("ateco")
            if isinstance(a, dict) and not b["codici_ateco"]:
                codici = [str(x).strip() for x in a.get("codici_ateco") or [] if _ATECO.match(str(x).strip())]
                if codici:
                    modifiche["codici_ateco"] = codici
                    if a.get("ateco_versione") in ("2007", "2025"):
                        modifiche["ateco_versione"] = a["ateco_versione"]
                    avvertenze.append(f"Codici ATECO ricavati dalla descrizione dei settori: '{(a.get('frase') or '')[:300]}'")
                    fonti["codici_ateco"] = a.get("fonte") or "descrizione dei settori"
                    conti["ateco"] += 1
            t = c.get("territorio")
            if isinstance(t, dict) and not b["territorio_regioni"] and not b["territorio_province"]:
                regioni = [x for x in t.get("territorio_regioni") or [] if x in campi.REGIONI]
                province = [str(x).upper() for x in t.get("territorio_province") or [] if re.fullmatch(r"[A-Za-z]{2}", str(x))]
                if regioni or province:
                    modifiche["territorio_regioni"], modifiche["territorio_province"] = regioni, province
                    fonti["territorio_regioni"] = t.get("fonte") or "testo del bando"
                    conti["territorio"] += 1
            if prova:
                print(f"[{bid}] {list(modifiche)}")
                continue
            if modifiche:
                dati.update({"avvertenze": avvertenze, "problemi": problemi, "fonti": fonti})
                modifiche["dati"] = json.dumps(dati)
                with conn.cursor() as cur:
                    cur.execute("SELECT set_config('bandi_radar.causa', %s, true)",
                                ("complemento della scheda in sessione del 03/10: " + ", ".join(k for k in modifiche if k != "dati"),))
                    cur.execute(f"UPDATE bandi SET {', '.join(f'{k} = %s' for k in modifiche)} WHERE id = %s", (*modifiche.values(), bid))
                conn.commit()
            (f.parent / "importato").write_text("")
    print(("PROVA " if prova else "") + str(conti))
    return 0


if __name__ == "__main__":
    sys.exit(main())
