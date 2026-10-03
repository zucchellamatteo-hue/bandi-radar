"""Punto 1 e 2 del piano del 03/10: salva gli esiti del ricontrollo dello stato (/out/stato/esiti/<id>.json).
- chiuso/esaurito: chiuso_il (la data trovata, o oggi), scadenza se mancava, avvertenza nella scheda;
- aperto/in_arrivo: apertura e scadenza solo se la scheda non le aveva;
- per_imprese 'no': preliminare.per_imprese = 'no' (il bando esce dai proponibili, la scheda resta nello storico).
Non cancella nulla; ogni modifica ha la sua causa nello storico delle versioni. Uso: importa_stato.py [--prova]"""
import json
import sys
from datetime import date
from pathlib import Path

from app.db.connessione import connetti
from app.schede.stato import aggiorna_stati

ESITI = Path("/out/stato/esiti")
FATTI = Path("/out/stato/importati.txt")


def data(x):
    try:
        return date.fromisoformat(x) if x else None
    except (TypeError, ValueError):
        return None


def main():
    prova = "--prova" in sys.argv
    oggi = date.today()
    fatti = set(FATTI.read_text().split()) if FATTI.exists() else set()
    conti = {}
    with connetti() as conn:
        for f in sorted(ESITI.glob("*.json"), key=lambda p: int(p.stem)):
            if f.stem in fatti:
                continue
            try:
                e = json.loads(f.read_text())
            except json.JSONDecodeError:
                print(f"[{f.stem}] json non valido")
                continue
            bid = int(f.stem)
            with conn.cursor() as cur:
                cur.execute("SELECT id, data_apertura, scadenza, chiuso_il, dati, preliminare FROM bandi WHERE id=%s", (bid,))
                b = cur.fetchone()
            stato = e.get("stato")
            conti[stato] = conti.get(stato, 0) + 1
            nota = (f"Ricontrollo della pagina ufficiale del {oggi:%d/%m/%Y}: {stato}. "
                    f"{e.get('motivo') or ''} «{(e.get('citazione') or '')[:300]}»").strip()
            modifiche = {}
            if stato in ("chiuso", "esaurito"):
                modifiche["chiuso_il"] = min(data(e.get("chiuso_il")) or oggi, oggi)
                if b["scadenza"] is None and data(e.get("scadenza")) and data(e.get("scadenza")) < oggi:
                    modifiche["scadenza"] = data(e.get("scadenza"))
            elif stato in ("aperto", "in_arrivo"):
                if b["data_apertura"] is None and data(e.get("apertura")):
                    modifiche["data_apertura"] = data(e.get("apertura"))
                if b["scadenza"] is None and data(e.get("scadenza")) and data(e.get("scadenza")) >= oggi:
                    modifiche["scadenza"] = data(e.get("scadenza"))
            if stato != "non_chiaro" or e.get("per_imprese") == "no":
                dati = b["dati"] or {}
                dati["avvertenze"] = [a for a in (dati.get("avvertenze") or []) if not str(a).startswith("Ricontrollo della pagina ufficiale")]
                if stato in ("chiuso", "esaurito") or e.get("per_imprese") == "no":
                    dati["avvertenze"].insert(0, nota)
                dati["ricontrollo_stato"] = {"il": oggi.isoformat(), **e}
                modifiche["dati"] = json.dumps(dati)
            if e.get("per_imprese") == "no" and b["preliminare"] is not None:
                pre = dict(b["preliminare"])
                pre["per_imprese"] = "no"
                pre["motivo"] = ("Ricontrollo 03/10: non per imprese. " + (e.get("motivo") or ""))[:500]
                modifiche["preliminare"] = json.dumps(pre)
                conti["non_per_imprese"] = conti.get("non_per_imprese", 0) + 1
            if prova:
                print(f"[{bid}] {stato} {e.get('per_imprese')} -> {list(modifiche)}")
                continue
            if modifiche:
                with conn.cursor() as cur:
                    cur.execute("SELECT set_config('bandi_radar.causa', %s, true)",
                                (f"ricontrollo dello stato sulla pagina ufficiale del {oggi:%d/%m/%Y}: {stato}",))
                    cur.execute(f"UPDATE bandi SET {', '.join(f'{k} = %s' for k in modifiche)} WHERE id = %s",
                                (*modifiche.values(), bid))
                conn.commit()
            with FATTI.open("a") as out:
                out.write(f"{bid}\n")
        if not prova:
            print("stati cambiati:", aggiorna_stati(conn))
    print(("PROVA " if prova else "") + str(conti))


if __name__ == "__main__":
    main()
