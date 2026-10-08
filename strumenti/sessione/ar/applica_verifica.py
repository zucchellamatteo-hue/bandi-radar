"""Applica le correzioni della verifica IA (campi colonna di bandi e, se presenti, in dati->risposta).
Uso: applica_verifica.py CARTELLA ID ...   (tutte le correzioni dei bandi indicati)

Dal 08/10: i campi di testo lungo (requisiti, cosa_finanzia) non si sostituiscono mai in automatico, perche' la
correzione di solito e' una frase da aggiungere (4181: i requisiti erano diventati una riga sola); ogni bando ha il
suo punto di salvataggio, cosi' un errore su un bando non annulla le correzioni degli altri (3548)."""
import json
import sys
from app.db.connessione import connetti

COLONNE = {"tipo_agevolazione", "contributo_massimo", "percentuale", "percentuale_fondo_perduto", "soggetti_ammessi",
           "forma_incentivo", "territorio_regioni", "scadenza", "data_apertura", "dotazione", "codici_ateco"}
TESTO = {"requisiti", "cosa_finanzia", "sintesi", "a_chi_si_rivolge"}
JSONB = {"forma_incentivo"}
ELENCHI = {"soggetti_ammessi", "territorio_regioni", "codici_ateco"}
cartella = sys.argv[1]
with connetti() as conn, conn.cursor() as cur:
    for arg in sys.argv[2:]:
        bid = int(arg.split(":")[0])
        d = json.load(open(f"/out/verifica/{cartella}/{bid}/verifica_ia.json"))
        cur.execute("SAVEPOINT bando")
        try:
            for p in d["problemi"]:
                c = p.get("correzione") or {}
                campo, valore = c.get("campo"), c.get("valore")
                if campo in TESTO:
                    print(bid, "da sistemare a mano (testo):", campo, "->", str(valore)[:120])
                    continue
                if campo not in COLONNE:
                    print(bid, "saltato (campo non gestito):", campo)
                    continue
                if campo in ELENCHI and isinstance(valore, str):
                    valore = json.loads(valore) if valore.strip().startswith("[") else [valore]
                cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"verifica IA ({cartella}): {campo}",))
                v = json.dumps(valore) if campo in JSONB else valore
                cur.execute(f"UPDATE bandi SET {campo} = %s WHERE id = %s", (v, bid))
                cur.execute("""UPDATE bandi SET dati = jsonb_set(dati, ARRAY['risposta', %s], %s::jsonb)
                               WHERE id = %s AND dati->'risposta' ? %s""", (campo, json.dumps(valore), bid, campo))
                print(bid, campo, "corretto")
            cur.execute("RELEASE SAVEPOINT bando")
        except Exception as exc:  # noqa: BLE001 - un bando sbagliato non ferma gli altri
            cur.execute("ROLLBACK TO SAVEPOINT bando")
            print(bid, "NON corretto (nessuna modifica salvata per questo bando):", exc)
    conn.commit()
