"""Salva gli smistamenti dei lotti compilati nella sessione del 28/09 (smista/lotto_NNN.json), con gli stessi
controlli del programma (ia.controlla_smistamento: tutti gli id, una volta sola, esiti ammessi). Sostituisce solo
le decisioni delle regole, mai quelle di Matteo. Chi manca resta "da rivedere".  importa_smista.py [--prova]"""
import json
import sys
from collections import Counter
from pathlib import Path

from app.db.connessione import connetti
from app.schede import ia

OUT = Path("/out/smista")
prova = "--prova" in sys.argv
conta = Counter()
with connetti() as conn:
    for f in sorted(OUT.glob("lotto_*.json")):
        ids = [int(x) for x in f.with_suffix(".ids").read_text().split()]
        try:
            risposta = json.loads(f.read_text())
        except json.JSONDecodeError:
            conta["json rotti"] += 1
            continue
        c = ia.controlla_smistamento(ids, risposta)
        conta["mancanti"] += len(c.mancanti)
        for esito, _ in c.decisi.values():
            conta[esito] += 1
        if prova:
            continue
        with conn.cursor() as cur:
            for i, (esito, motivo) in c.decisi.items():
                cur.execute(
                    """UPDATE smistamenti SET esito = %s, motivo = %s, deciso_da = 'ia', costo = 0, deciso_il = now()
                       WHERE annuncio_id = %s AND deciso_da = 'regole'""",
                    (esito, f"IA (sessione del 28/09/2026, Opus, senza API): {motivo}", i))
        conn.commit()
        f.rename(f.with_suffix(".importato"))
print(("PROVA: " if prova else "") + ", ".join(f"{k} {v}" for k, v in conta.items()))
