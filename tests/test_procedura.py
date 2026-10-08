"""Procedura nuova del regista (app/catena/procedura.py): documento verificato e secondo controllo prima di proporre."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

from app.catena import procedura

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")

SI = {"verificato": "si", "nome": "Avviso 2026", "deciso_da": "sessione"}
CONTROLLO = {"esito": "corretta", "gravi": 0, "fatto_il": "2026-10-08T12:00:00+00:00", "da": "sessione"}

# (nome, colonne, esito atteso)
CASI = [
    ("niente", {}, "documento_da_verificare"),
    ("documento di un altro bando", {"verifica_documento": {"verificato": "no", "problema": "altro_bando"}}, "da_recuperare"),
    ("solo documento", {"verifica_documento": SI}, "secondo_controllo_da_fare"),
    ("controllo prima della scheda nuova", {"verifica_documento": SI, "secondo_controllo": CONTROLLO,
                                            "scheda_il": "2026-10-09T08:00:00+00:00"}, "secondo_controllo_da_fare"),
    ("grave non corretto", {"verifica_documento": SI, "secondo_controllo": {**CONTROLLO, "esito": "grave", "gravi": 1}},
     "errori_da_correggere"),
    ("grave corretto", {"verifica_documento": SI, "secondo_controllo": {**CONTROLLO, "esito": "grave", "gravi": 1,
                                                                        "correzioni_applicate": True}}, "pronto"),
    ("tutto fatto", {"verifica_documento": SI, "secondo_controllo": CONTROLLO,
                     "scheda_il": "2026-10-01T08:00:00+00:00"}, "pronto"),
    ("minori da sistemare", {"verifica_documento": SI, "secondo_controllo": {**CONTROLLO, "esito": "da_correggere"}}, "pronto"),
]


@pytest.mark.parametrize("nome,colonne,atteso", CASI, ids=[c[0] for c in CASI])
def test_esito(nome, colonne, atteso):
    e, motivo = procedura.esito(colonne)
    assert e == atteso and motivo


def test_motivo_da_recuperare_dice_perche():
    _, motivo = procedura.esito({"verifica_documento": {"verificato": "no", "problema": "edizione_vecchia",
                                                        "motivo": "avviso 2025"}})
    assert "edizione passata" in motivo and "avviso 2025" in motivo


def _importa_verifica():
    percorso = Path(__file__).resolve().parents[1] / "strumenti/sessione/ar/importa_verifica.py"
    spec = importlib.util.spec_from_file_location("importa_verifica", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_lettura_della_verifica(tmp_path):
    iv = _importa_verifica()
    f = tmp_path / "123" / "verifica_ia.json"
    f.parent.mkdir()
    f.write_text(json.dumps({"id": 123, "tipo_procedura": "sportello", "esito": "grave",
                             "documento": {"verificato": "no", "problema": "inventato", "motivo": "x"},
                             "problemi": [{"gravita": "grave"}, {"gravita": "minore"}]}))
    r = iv.leggi(f, "giro", corrette=True)
    assert r["id"] == 123 and r["tipo_procedura"] == "sportello"
    assert r["secondo_controllo"]["gravi"] == 1 and r["secondo_controllo"]["minori"] == 1
    assert r["secondo_controllo"]["correzioni_applicate"] is True
    assert r["verifica_documento"]["problema"] == "manca"     # valore fuori elenco: il caso piu' prudente
    vecchia = tmp_path / "124" / "verifica_ia.json"            # verifiche prima del 08/10: niente tipo ne' documento
    vecchia.parent.mkdir()
    vecchia.write_text(json.dumps({"id": 124, "esito": "corretta", "problemi": []}))
    r = iv.leggi(vecchia, "giro", corrette=False)
    assert r["verifica_documento"] is None and r["tipo_procedura"] is None
    assert r["secondo_controllo"]["correzioni_applicate"] is False


@db
def test_sql_uguale_al_python():
    """ESITO_SQL e procedura.esito danno la stessa risposta su ogni caso."""
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            for nome, colonne, atteso in CASI:
                cur.execute(f"""SELECT {procedura.ESITO_SQL} AS esito FROM (SELECT %s::jsonb AS verifica_documento,
                                       %s::jsonb AS secondo_controllo, %s::timestamptz AS scheda_il) b""",
                            (json.dumps(colonne.get("verifica_documento")), json.dumps(colonne.get("secondo_controllo")),
                             colonne.get("scheda_il")))
                assert cur.fetchone()["esito"] == atteso, nome
        conn.rollback()
