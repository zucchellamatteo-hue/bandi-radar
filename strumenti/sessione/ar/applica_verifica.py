"""Applica le correzioni della verifica IA (campi colonna di bandi e, se presenti, in dati->risposta).
Uso: applica_verifica.py CARTELLA ID[:gravi|tutte] ...   (default: tutte le correzioni del bando)"""
import json
import sys
from app.db.connessione import connetti

COLONNE = {"tipo_agevolazione", "contributo_massimo", "percentuale", "percentuale_fondo_perduto", "soggetti_ammessi",
           "forma_incentivo", "scadenza", "data_apertura", "requisiti", "dotazione", "codici_ateco"}
JSONB = {"forma_incentivo"}
cartella = sys.argv[1]
with connetti() as conn, conn.cursor() as cur:
    for arg in sys.argv[2:]:
        bid = int(arg.split(":")[0])
        d = json.load(open(f"/out/verifica/{cartella}/{bid}/verifica_ia.json"))
        for p in d["problemi"]:
            c = p.get("correzione") or {}
            campo, valore = c.get("campo"), c.get("valore")
            if campo not in COLONNE:
                print(bid, "saltato (campo non gestito):", campo)
                continue
            cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"verifica IA ({cartella}): {campo}",))
            v = json.dumps(valore) if campo in JSONB else valore
            cur.execute(f"UPDATE bandi SET {campo} = %s WHERE id = %s", (v, bid))
            cur.execute("""UPDATE bandi SET dati = jsonb_set(dati, ARRAY['risposta', %s], %s::jsonb)
                           WHERE id = %s AND dati->'risposta' ? %s""", (campo, json.dumps(valore), bid, campo))
            print(bid, campo, "corretto")
    conn.commit()
