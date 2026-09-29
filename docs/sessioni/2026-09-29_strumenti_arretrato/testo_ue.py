"""Una tantum (28/09): rilegge la scorta del Portale UE e aggiunge dati.testo agli annunci gia' raccolti
(l'upsert della raccolta non tocca i dati se titolo e riassunto non cambiano). Tocca solo il campo testo."""
import json

from app.db.connessione import connetti
from app.fonti.registro import carica_registro
from app.raccolta.esegui import leggi_tutta
from app.raccolta.scarica import nuovo_client

fonte = {f.id: f for f in carica_registro()}["ue_funding_tenders_api"]
with nuovo_client() as c:
    lettura = leggi_tutta(fonte, c)
print(lettura.messaggio)
aggiornati = 0
with connetti() as conn, conn.cursor() as cur:
    for a in lettura.annunci:
        testo = (a.dati or {}).get("testo")
        if not testo:
            continue
        cur.execute("""UPDATE annunci SET dati = coalesce(dati, '{}'::jsonb) || jsonb_build_object('testo', %s::text)
                       WHERE fonte_id = %s AND url = %s""", (testo, fonte.id, a.url))
        aggiornati += cur.rowcount
    conn.commit()
print(f"annunci aggiornati con il testo: {aggiornati}")
