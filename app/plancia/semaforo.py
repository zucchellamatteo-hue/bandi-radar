"""Stato di una fonte per la plancia: verde, giallo, rosso o pausa, con la spiegazione.

Regole (§5 del piano):
- pausa: fonte messa in pausa dalla plancia, oppure esclusa dal registro.
- rosso: ultimo controllo con struttura cambiata, oppure 3 errori di fila.
- giallo: 1 o 2 errori di fila; oppure silenzio sospetto (nessuna novita' da piu' di 3 volte l'intervallo
  normale della fonte, minimo 30 giorni); oppure mai controllata; oppure risponde ma non se n'e' mai letto nulla
  (voce del registro da controllare, da non confondere con una fonte tranquilla).
- verde: tutto il resto.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

INTERVALLO_GIORNI = {"giornaliera": 1, "tre_a_settimana": 2.33, "settimanale": 7, "quindicinale": 14, "mensile": 30}
MINIMO_SILENZIO_GIORNI = 30
ERRORI_PER_ROSSO = 3


@dataclass
class Stato:
    colore: str          # verde | giallo | rosso | pausa
    motivo: str
    silenzio_giorni: int | None   # giorni dall'ultima novita' (None se mai)
    soglia_silenzio_giorni: int   # oltre questa soglia il silenzio e' sospetto


def calcola(frequenza: str, stato_registro: str, in_pausa: bool, ultimi_esiti: list[str],
            ultima_novita: datetime | None, adesso: datetime, elementi_ultimo: int | None = None) -> Stato:
    """ultimi_esiti: esiti degli ultimi controlli, dal piu' recente; elementi_ultimo: elementi letti dall'ultimo.
    Una fonte che risponde ma da cui non si e' mai letto nulla non e' una fonte tranquilla: va guardata la voce."""
    soglia = max(MINIMO_SILENZIO_GIORNI, int(3 * INTERVALLO_GIORNI.get(frequenza, 7)))
    silenzio = (adesso - ultima_novita).days if ultima_novita else None

    if in_pausa or stato_registro == "esclusa":
        return Stato("pausa", "in pausa" if in_pausa else "esclusa dal registro", silenzio, soglia)
    if not ultimi_esiti:
        return Stato("giallo", "mai controllata", silenzio, soglia)
    if ultimi_esiti[0] == "struttura_cambiata":
        return Stato("rosso", "struttura cambiata: la pagina risponde ma non si legge piu' nulla", silenzio, soglia)
    errori_di_fila = 0
    for e in ultimi_esiti:
        if e == "errore":
            errori_di_fila += 1
        else:
            break
    if errori_di_fila >= ERRORI_PER_ROSSO:
        return Stato("rosso", f"{errori_di_fila} errori di fila", silenzio, soglia)
    if errori_di_fila:
        return Stato("giallo", f"{errori_di_fila} error{'e' if errori_di_fila == 1 else 'i'} all'ultimo controllo", silenzio, soglia)
    if ultimi_esiti[0] == "saltato":
        return Stato("giallo", "saltata all'ultimo controllo (robots.txt o modalita' non disponibile)", silenzio, soglia)
    if silenzio is not None and silenzio > soglia:
        return Stato("giallo", f"silenzio sospetto: nessuna novita' da {silenzio} giorni (soglia {soglia})", silenzio, soglia)
    if silenzio is None and elementi_ultimo == 0:
        return Stato("giallo", "risponde ma non si legge nulla: controllare la voce del registro", silenzio, soglia)
    if silenzio is None:
        return Stato("giallo", "nessuna novita' trovata finora", silenzio, soglia)
    return Stato("verde", "regolare", silenzio, soglia)
