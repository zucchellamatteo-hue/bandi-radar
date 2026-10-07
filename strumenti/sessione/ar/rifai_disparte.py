"""Rifa' pagina ufficiale e documenti dei bandi aperti "in disparte" non UE, DOPO l'unione delle correzioni del 08/10
(PIANO_QUALITA azione 2: link a file senza estensione, formato dai primi byte, <form> ASP.NET, falso login, Plone per
sito, pagine "atto", ordine prima del limite dei 30 file).

Da lanciare con il codice di produzione aggiornato (dopo il deploy):
    /tmp/claude-1000/ar.sh rifai_disparte.py --prova            # stampa soltanto: quali bandi, nessuna rete, nessuna scrittura
    /tmp/claude-1000/ar.sh rifai_disparte.py --limite 20        # i primi 20, per vedere come va
    /tmp/claude-1000/ar.sh rifai_disparte.py                    # tutti (circa 410: con le pause, un paio d'ore)
    /tmp/claude-1000/ar.sh rifai_disparte.py --bando 920        # uno solo
    /tmp/claude-1000/ar.sh rifai_disparte.py --senza-altro      # salta la rilettura dei file "altro" (passo 1)

Passi:
  1. rilegge una volta i file "altro" gia' scaricati (allegati --rileggi-altro: PDF di myCIVIS e simili);
  2. per ogni bando: rimette pagina_cercata_il e allegati_cercati_il a NULL, rifa' la ricerca della pagina ufficiale
     (la salva solo se la trova: una pagina che oggi non risponde non fa perdere quella buona), poi i documenti; se
     arrivano documenti nuovi `documentazione` torna NULL (salva_bando);
  3. rifa' il filtro "c'e' il bando?" sui bandi con documentazione NULL e stampa quanti sono passati a "bando".
"""
import argparse
import sys

from app.db.blocchi import blocco
from app.db.connessione import connetti
from app.fonti.registro import CARTELLA_FONTI, carica_registro
from app.raccolta.scarica import nuovo_client
from app.schede import allegati, documentazione, pagina_ufficiale as pu

SCELTA = """SELECT b.id, b.titolo, b.url, b.documentazione, s.fase
            FROM bandi_situazione s JOIN bandi b ON b.id = s.id
            WHERE s.situazione = 'in_disparte' AND b.stato IN ('aperto', 'in_arrivo') AND b.unito_a IS NULL
              AND coalesce(b.url, '') NOT LIKE '%%ec.europa.eu%%'
              AND NOT EXISTS (SELECT 1 FROM annunci a WHERE a.bando_id = b.id AND a.fonte_id = 'ue_funding_tenders_api')
              {filtro}
            ORDER BY b.id"""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--prova", action="store_true", help="stampa soltanto: nessuna rete, nessuna scrittura")
    p.add_argument("--limite", type=int, default=0, help="al massimo N bandi")
    p.add_argument("--bando", type=int, help="solo questo bando")
    p.add_argument("--senza-altro", action="store_true", help="non rileggere i file 'altro' (passo 1)")
    args = p.parse_args()

    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute(SCELTA.format(filtro="AND b.id = %s" if args.bando else ""), (args.bando,) if args.bando else ())
            bandi = [dict(r) for r in cur.fetchall()]
            if args.limite:
                bandi = bandi[:args.limite]
            cur.execute("SELECT count(*) AS n FROM allegati WHERE tipo = 'altro' AND errore IS NULL AND percorso_locale IS NOT NULL")
            altro = cur.fetchone()["n"]
            ids = [b["id"] for b in bandi]
            cur.execute("SELECT documentazione, count(*) AS n FROM bandi WHERE id = ANY(%s) GROUP BY 1", (ids,))
            prima = {r["documentazione"]: r["n"] for r in cur.fetchall()}
        print(f"Bandi aperti in disparte non UE da rifare: {len(bandi)} (documentazione oggi: {prima})")
        print(f"File 'altro' da rileggere (passo 1): {0 if args.senza_altro else altro}")
        if args.prova:
            for b in bandi:
                print(f"  [{b['id']}] {b['fase']:22} {str(b['documentazione']):8} {b['titolo'][:60]} | {(b['url'] or '-')[:90]}")
            print("PROVA: nessuna modifica, nessuna richiesta ai siti.")
            return 0

        with blocco("rifai_disparte") as preso:
            if not preso:
                return 1
            if not args.senza_altro:
                allegati.rileggi_altro()

            registro = carica_registro(CARTELLA_FONTI)
            regole = {f.id: {**f.pagina_ufficiale, **({"documenti": "plone_api"} if f.documenti_plone else {}),
                             **({"_ignora_robots": True} if f.ignora_robots else {})} for f in registro}
            indirizzi = {f.id: f.url for f in registro if f.url}
            siti_plone = allegati.domini_plone(registro)
            cambiate = con_nuovi = saltati = 0
            with nuovo_client() as client:
                pausa = allegati.Pausa(client)
                for n, b in enumerate(bandi, start=1):
                    with conn.cursor() as cur:
                        cur.execute("UPDATE bandi SET pagina_cercata_il = NULL, allegati_cercati_il = NULL WHERE id = %s",
                                    (b["id"],))
                        documenti_prima = allegati.impronte_documenti(cur, b["id"])
                    conn.commit()
                    esito = pu.esegui_regole(client, pausa, pu.annunci_del_bando(conn, b["id"]), regole, indirizzi, siti_plone)
                    if esito.stato == "trovata":
                        pu.salva(conn, b["id"], esito)
                        if esito.url != b["url"]:
                            cambiate += 1
                            print(f"  [{b['id']}] pagina nuova: {esito.url}")
                    else:   # si tiene la pagina di prima
                        with conn.cursor() as cur:
                            cur.execute("UPDATE bandi SET pagina_cercata_il = now() WHERE id = %s", (b["id"],))
                        conn.commit()
                    allegati.esegui(bando_id=b["id"])
                    with conn.cursor() as cur:
                        cur.execute("SELECT allegati_cercati_il FROM bandi WHERE id = %s", (b["id"],))
                        if cur.fetchone()["allegati_cercati_il"] is None:
                            saltati += 1   # allegati in corso nel regista: il bando resta in coda, lo fa il regista
                        nuovi = allegati.impronte_documenti(cur, b["id"]) - documenti_prima
                        if nuovi:
                            con_nuovi += 1
                            cur.execute("UPDATE bandi SET documentazione = NULL WHERE id = %s", (b["id"],))
                    conn.commit()
                    print(f"[{n}/{len(bandi)}] bando {b['id']}: pagina {esito.stato}, {len(nuovi)} documenti nuovi", flush=True)
            print(f"Pagine ufficiali cambiate: {cambiate}; bandi con documenti nuovi: {con_nuovi}; "
                  f"saltati (allegati in corso altrove, restano in coda): {saltati}")

    documentazione.esegui()
    with connetti() as conn, conn.cursor() as cur:
        cur.execute("SELECT documentazione, count(*) AS n FROM bandi WHERE id = ANY(%s) GROUP BY 1", (ids,))
        print(f"Documentazione prima: {prima}; dopo: { {r['documentazione']: r['n'] for r in cur.fetchall()} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
