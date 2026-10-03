"""Punto 3 del piano del 03/10: riclassifica i documenti gia' scaricati con la nuova categoria_allegato (nome + testo).
Uso: riclassifica.py [--scrivi]. Stampa i cambi e i bandi proponibili non chiusi che hanno documenti cambiati."""
import sys
from collections import Counter

from app.db.connessione import connetti
from app.schede.allegati import categoria_allegato

scrivi = "--scrivi" in sys.argv
cambi, bandi = Counter(), set()
with connetti() as conn, conn.cursor() as cur:
    cur.execute("""SELECT a.id, a.bando_id, a.nome, a.url, a.tipo, a.categoria, a.testo_estratto,
                          b.completezza = 'bando_ufficiale' AND coalesce(b.stato,'x') <> 'chiuso' AS aperto
                   FROM allegati a LEFT JOIN bandi b ON b.id = a.bando_id WHERE a.categoria = 'modulistica'""")
    righe = cur.fetchall()
    esempi = []
    for r in righe:
        nuova = categoria_allegato(r["nome"], r["url"], r["tipo"], r["testo_estratto"])
        if nuova != r["categoria"]:
            cambi[f"{r['categoria']} -> {nuova}"] += 1
            if r["aperto"]:
                bandi.add(r["bando_id"])
            if len(esempi) < 25:
                esempi.append(f"  [{r['bando_id']}] {r['nome'][:80]} -> {nuova}")
            if scrivi:
                cur.execute("UPDATE allegati SET categoria = %s WHERE id = %s", (nuova, r["id"]))
    if scrivi:
        conn.commit()
print("modulistica esaminati:", len(righe), dict(cambi))
print("\n".join(esempi))
print("bandi proponibili non chiusi toccati:", len(bandi), sorted(bandi))
