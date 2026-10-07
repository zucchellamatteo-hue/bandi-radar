"""Script di sessione che ricava i destinatari dei bandi decisi prima del 07/10, senza IA (prudente: nel dubbio
"da_determinare"). Mai cambiare per_imprese."""

import importlib.util
from pathlib import Path

_PERCORSO = Path(__file__).resolve().parent.parent / "strumenti/sessione/ar/deriva_destinatari.py"
_spec = importlib.util.spec_from_file_location("deriva_destinatari", _PERCORSO)
deriva_destinatari = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deriva_destinatari)
deriva = deriva_destinatari.deriva


def _d(motivo, per_imprese="no", soggetti=None, a_chi=None):
    return deriva({"per_imprese": per_imprese, "motivo": motivo}, soggetti, a_chi)[0]


def test_per_imprese_si_e_incerto():
    assert _d("ok", "si", ["impresa", "ente_terzo_settore"]) == {"destinatari": ["imprese", "non_profit"]}
    assert _d("non chiaro", "incerto") == {"destinatari": ["da_determinare"]}


def test_non_per_imprese():
    assert _d("Beneficiari sono solo enti del Terzo settore iscritti al RUNTS")["destinatari"] == ["non_profit"]
    assert _d("Solo enti pubblici e organizzazioni senza scopo di lucro")["destinatari"] == ["non_profit", "enti_pubblici"]
    assert _d("Beneficiari esclusivamente Comuni e Unioni di Comuni")["destinatari"] == ["enti_pubblici"]
    assert _d("Contributo prima casa per giovani coppie")["destinatari"] == ["persone_fisiche"]
    assert _d("È una gara d'appalto per l'affidamento di un servizio") == {"destinatari": [], "agevolazione": "no"}
    # nel dubbio: da determinare
    assert _d("Destinatari esclusivamente gli Enti locali; le imprese del terzo settore sono solo destinatarie "
              "indirette")["destinatari"] == ["da_determinare"]
    assert _d("Beneficiari solo enti di formazione accreditati")["destinatari"] == ["da_determinare"]
    assert _d("Bando per scavi archeologici")["destinatari"] == ["da_determinare"]
    # i soggetti della scheda contano
    assert _d("non per imprese", soggetti=["ente_terzo_settore"])["destinatari"] == ["non_profit"]
