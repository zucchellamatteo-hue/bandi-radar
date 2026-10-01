"""Blocchi nel database: lo stesso lavoro non gira due volte insieme (02/10/2026, dall'analisi della struttura).

Prima un comando lanciato a mano e il giro del regista potevano scegliere gli stessi bandi (scaricamenti doppi,
chiamate all'IA pagate due volte). Ora ogni passo prende un blocco con il suo nome: se e' gia' preso da un altro
processo, il secondo salta il passo e lo dice. I blocchi si liberano da soli se il processo muore (advisory lock di
Postgres, legato alla connessione).

    with blocco("allegati") as preso:
        if not preso:
            return 0
        ...
"""

from __future__ import annotations

import zlib
from contextlib import contextmanager


def _chiave(nome: str) -> int:
    return zlib.crc32(f"bandi-radar:{nome}".encode()) & 0x7FFFFFFF


@contextmanager
def blocco(nome: str):
    """Rende True se il blocco e' preso (e lo tiene fino all'uscita), False se un altro processo ce l'ha gia'."""
    from app.db.connessione import connetti

    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(%s) AS preso", (_chiave(nome),))
            preso = bool(cur.fetchone()["preso"])
        conn.commit()
        if not preso:
            print(f"'{nome}' e' gia' in corso in un altro processo: questo passo si salta.", flush=True)
        try:
            yield preso
        finally:
            if preso:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_unlock(%s)", (_chiave(nome),))
                conn.commit()


def con_blocco(nome: str, valore_se_occupato=0):
    """Decoratore: la funzione gira solo se prende il blocco `nome`, altrimenti rende `valore_se_occupato`."""
    def decora(funzione):
        def avvolta(*args, **kwargs):
            with blocco(nome) as preso:
                if not preso:
                    return valore_se_occupato
                return funzione(*args, **kwargs)
        avvolta.__name__, avvolta.__doc__, avvolta.__wrapped__ = funzione.__name__, funzione.__doc__, funzione
        return avvolta
    return decora
