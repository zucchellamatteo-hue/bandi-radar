"""Controlli sul registro delle fonti: formato dei file e regole di validazione."""

from pathlib import Path

import pytest

from app.fonti.registro import CARTELLA_FONTI, ErroreRegistro, carica_registro

VOCE_OK = """
- id: prova_ok
  nome: Prova
  ente: Ente di prova
  tipo: regione
  territorio: LOM
  url: https://esempio.it/bandi
  modalita: html
  frequenza: settimanale
  stato: attiva
  verificato_il: 2026-09-24
  note: voce di prova
"""


def _scrivi(cartella: Path, nome: str, testo: str) -> None:
    (cartella / nome).write_text(testo, encoding="utf-8")


def test_il_registro_del_repository_e_valido():
    fonti = carica_registro(CARTELLA_FONTI)
    assert fonti, "il registro non deve essere vuoto"
    assert len({f.id for f in fonti}) == len(fonti)


def test_voce_corretta(tmp_path):
    _scrivi(tmp_path, "a.yaml", VOCE_OK)
    (fonte,) = carica_registro(tmp_path)
    assert fonte.id == "prova_ok"
    assert fonte.verificato_il.isoformat() == "2026-09-24"
    assert fonte.indirizzo_da_controllare == "https://esempio.it/bandi"


def test_feed_preferito_alla_pagina(tmp_path):
    _scrivi(tmp_path, "a.yaml", VOCE_OK.replace("modalita: html", "modalita: rss\n  feed_url: https://esempio.it/feed"))
    (fonte,) = carica_registro(tmp_path)
    assert fonte.indirizzo_da_controllare == "https://esempio.it/feed"


@pytest.mark.parametrize(
    "modifica, frammento",
    [
        (("tipo: regione", "tipo: comune"), "tipo 'comune' non ammesso"),
        (("modalita: html", "modalita: rss"), "richiede feed_url"),
        (("url: https://esempio.it/bandi", "url: esempio.it/bandi"), "deve iniziare con http"),
        (("id: prova_ok", "id: Prova-OK"), "id non valido"),
        (("verificato_il: 2026-09-24", "verificato_il: ieri"), "AAAA-MM-GG"),
        (("  note: voce di prova", "  note: x\n  colore: blu"), "campi non previsti: colore"),
    ],
)
def test_voce_errata(tmp_path, modifica, frammento):
    _scrivi(tmp_path, "a.yaml", VOCE_OK.replace(*modifica))
    with pytest.raises(ErroreRegistro, match=frammento):
        carica_registro(tmp_path)


def test_id_duplicato_tra_file(tmp_path):
    _scrivi(tmp_path, "a.yaml", VOCE_OK)
    _scrivi(tmp_path, "b.yaml", VOCE_OK)
    with pytest.raises(ErroreRegistro, match="gia' usato"):
        carica_registro(tmp_path)
