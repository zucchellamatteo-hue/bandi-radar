"""Situazione dei bandi (vista bandi_situazione, app/catena/situazione.py): una sola voce per bando, con il perche'."""

import json
import os
from pathlib import Path

import pytest

from app.catena import situazione

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")

PASSA = {"per_imprese": "si", "edizione_in_corso": "si", "stato": "aperto", "testo_bando": "si", "motivo": "bando aperto"}

# (nome, colonne del bando, situazione attesa, fase attesa, chi ha deciso atteso)
CASI = [
    ("pagina", {}, "in_lavorazione", "pagina_da_cercare", None),
    ("non trovata", {"pagina_stato": "non_trovata", "pagina_motivo": "nessun link"}, "in_lavorazione", "pagina_non_trovata", None),
    ("documenti", {"pagina_stato": "trovata"}, "in_lavorazione", "documenti_da_scaricare", None),
    ("filtro", {"pagina_stato": "trovata", "allegati_cercati_il": "now"}, "in_lavorazione", "filtro_da_fare", None),
    ("in coda", {"pagina_stato": "trovata", "allegati_cercati_il": "now", "documentazione": "bando"},
     "in_lavorazione", "preliminare_in_coda", None),
    ("scheda in coda", {"pagina_stato": "trovata", "allegati_cercati_il": "now", "documentazione": "bando", "preliminare": PASSA},
     "in_lavorazione", "scheda_in_coda", None),
    ("seconda lettura", {"documentazione": "bando", "preliminare": {**PASSA, "stato": "chiuso", "seconda_lettura": "da_fare"}},
     "in_lavorazione", "seconda_lettura_in_coda", "ia"),
    ("segnali", {"documentazione": "bando", "preliminare": {**PASSA, "stato": "chiuso", "deciso_da": "segnali",
                                                           "deciso_il": "2026-10-01T10:00:00+00:00",
                                                           "motivo": "segnali gratuiti, senza IA: scadenza passata"}},
     "scartato_chiuso", "chiuso", "segnali"),
    ("edizione", {"documentazione": "sintesi", "preliminare": {**PASSA, "edizione_in_corso": "no",
                                                              "compilato_da": "claude-code (sessione del 28/09/2026)"}},
     "scartato_chiuso", "edizione_passata", "sessione"),
    ("non imprese", {"documentazione": "bando", "preliminare": {**PASSA, "per_imprese": "no", "motivo": "per i Comuni"}},
     "scartato_non_per_imprese", "prima_della_scheda", "ia"),
    ("non imprese con scheda", {"completezza": "bando_ufficiale", "stato": "aperto", "dati": {"modello": "claude-opus-5-5"},
                                "preliminare": {**PASSA, "per_imprese": "no", "motivo": "Ricontrollo 03/10: non per imprese."}},
     "scartato_non_per_imprese", "dopo_la_scheda", "sessione"),
    ("senza testo", {"documentazione": "bando", "preliminare": {**PASSA, "testo_bando": "no"}}, "scartato_altro",
     "senza_testo_del_bando", "ia"),
    ("sintesi", {"pagina_stato": "trovata", "allegati_cercati_il": "now", "documentazione": "sintesi",
                 "documentazione_motivo": "solo pagine web"}, "in_disparte", "senza_scheda_sintesi", "regole"),
    ("scheda su sintesi", {"completezza": "solo_sintesi", "stato": "aperto", "dati": {"modello": "claude-code (sessione)"}},
     "in_disparte", "scheda_solo_sintesi", "sessione"),
    ("proponibile", {"completezza": "bando_ufficiale", "stato": "aperto", "dati": {"modello": "claude-opus-5-5"}},
     "proponibile", "scheda_pronta", "ia"),
    ("senza stato", {"completezza": "bando_ufficiale", "controllo": {"gravi": [], "da_migliorare": ["x"]}},
     "proponibile", "scheda_pronta", None),
    ("da aggiornare", {"completezza": "bando_ufficiale", "stato": "in_arrivo", "da_aggiornare": "proroga"},
     "proponibile", "scheda_da_aggiornare", None),
    ("errori", {"completezza": "bando_ufficiale", "stato": "aperto",
                "controllo": {"fatto_il": "2026-10-06T10:00:00+00:00", "gravi": ["scadenza prima dell'apertura"]}},
     "nascosto_per_errori", "problemi_gravi", "regole"),
    ("chiuso con scheda", {"completezza": "bando_ufficiale", "stato": "chiuso", "scadenza": "2026-01-31",
                           "controllo": {"gravi": ["x"]}}, "chiuso_con_scheda", "scaduto", "regole"),
]


def _inserisci(cur, titolo: str, colonne: dict) -> int:
    valori = {k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in colonne.items()}
    nomi = ["titolo", *valori]
    segnaposto = ["%s"] + ["now()" if v == "now" else "%s" for v in valori.values()]
    parametri = [titolo] + [v for v in valori.values() if v != "now"]
    cur.execute(f"INSERT INTO bandi ({', '.join(nomi)}) VALUES ({', '.join(segnaposto)}) RETURNING id", parametri)
    return cur.fetchone()["id"]


def test_ogni_situazione_ha_nome_e_ogni_fase_un_nome():
    assert len({k for k, _, _ in situazione.SITUAZIONI}) == len(situazione.SITUAZIONI)
    sql = (Path(__file__).resolve().parent.parent / "app/db/migrazioni/028_bandi_situazione.sql").read_text(encoding="utf-8")
    for chiave in situazione.NOMI:
        assert f"'{chiave}'" in sql
    for fase in situazione.FASI:
        assert fase in sql or fase.startswith(("scheda_", "senza_scheda_"))


@db
def test_una_situazione_per_bando_con_il_perche():
    from app.abbinamento import catalogo
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        ids: dict[str, int] = {}
        with conn.cursor() as cur:
            for nome, colonne, *_ in CASI:
                ids[nome] = _inserisci(cur, f"situazione di prova: {nome}", colonne)
            principale = ids["proponibile"]
            ids["unito"] = _inserisci(cur, "situazione di prova: unito", {"completezza": "bando_ufficiale", "stato": "aperto"})
            cur.execute("UPDATE bandi SET unito_a = %s WHERE id = %s", (principale, ids["unito"]))
        conn.commit()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM bandi_situazione WHERE id = ANY(%s)", (list(ids.values()),))
                righe = {r["id"]: r for r in cur.fetchall()}
            assert len(righe) == len(ids)                                   # una riga, quindi una situazione, per bando
            for nome, _, attesa, fase, chi in CASI:
                r = righe[ids[nome]]
                assert (r["situazione"], r["fase"], r["deciso_da"]) == (attesa, fase, chi), nome
                assert r["situazione"] in situazione.NOMI and r["fase"] in situazione.FASI, nome
            u = righe[ids["unito"]]
            assert u["situazione"] == "unito" and str(principale) in u["motivo"] and u["deciso_il"] is not None
            assert "scadenza passata" in righe[ids["segnali"]]["motivo"]
            assert righe[ids["segnali"]]["deciso_il"].isoformat().startswith("2026-10-01")
            assert righe[ids["non imprese"]]["motivo"] == "per i Comuni"
            assert "prima dell'apertura" in righe[ids["errori"]]["motivo"]
            assert righe[ids["chiuso con scheda"]]["motivo"].startswith("scaduto il 31/01/2026")
            assert righe[ids["non trovata"]]["motivo"] == "nessun link"
            assert righe[ids["da aggiornare"]]["motivo"] == "proroga"

            # La stessa definizione del catalogo: proponibile = nel catalogo, proponibile e non chiuso.
            per_catalogo = {b["id"] for b in catalogo.carica_bandi(conn)
                            if catalogo.proponibile(b) and b["stato"] != "chiuso" and b["id"] in righe}
            assert per_catalogo == {i for i, r in righe.items() if r["situazione"] == "proponibile"}

            # Conteggi ed elenchi del modulo (quelli della plancia e del comando per gli agenti).
            c = situazione.conteggi(conn)
            assert [v["situazione"] for v in c["situazioni"]] == [k for k, _, _ in situazione.SITUAZIONI]
            assert c["totale"] == sum(v["n"] for v in c["situazioni"]) and c["totale"] >= len(ids)
            chiusi = situazione.elenco(conn, "scartato_chiuso", "chiuso")
            assert ids["segnali"] in [r["id"] for r in chiusi] and ids["edizione"] not in [r["id"] for r in chiusi]
            r = situazione.di_un_bando(conn, ids["segnali"])
            assert r["chi"] == situazione.CHI["segnali"] and r["nome_situazione"] == "Scartati: chiusi"
        finally:
            with conn.cursor() as cur:
                cur.execute("UPDATE bandi SET unito_a = NULL WHERE id = ANY(%s)", (list(ids.values()),))
                cur.execute("DELETE FROM bandi WHERE id = ANY(%s)", (list(ids.values()),))
            conn.commit()


@db
def test_api_e_comando(capsys):
    from conftest import accesso_di_prova
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.main import app

    with connetti() as conn, conn.cursor() as cur:
        bando = _inserisci(cur, "situazione di prova: api", {"documentazione": "bando", "preliminare": {
            **PASSA, "stato": "chiuso", "deciso_da": "segnali", "motivo": "segnali gratuiti, senza IA: Bando Chiuso"}})
        conn.commit()
    try:
        c = TestClient(app)
        assert c.get("/api/situazione").status_code == 401
        assert c.get("/api/situazione", auth=accesso_di_prova("revisore")).status_code == 403    # serve "lavoro"
        admin = accesso_di_prova("admin")
        conti = c.get("/api/situazione", auth=admin).json()
        assert any(v["situazione"] == "scartato_chiuso" and v["n"] >= 1 for v in conti["situazioni"])
        righe = c.get("/api/situazione/scartato_chiuso?fase=chiuso", auth=admin).json()
        mio = next(r for r in righe if r["id"] == bando)
        assert mio["motivo"].endswith("Bando Chiuso") and mio["chi"] == situazione.CHI["segnali"]
        assert c.get("/api/situazione/inventata", auth=admin).status_code == 404
        assert c.get(f"/api/bandi/{bando}", auth=admin).json()["situazione"]["situazione"] == "scartato_chiuso"

        assert situazione.main([]) == 0
        assert "Scartati: chiusi" in capsys.readouterr().out
        assert situazione.main(["--situazione", "scartato_chiuso", "--limite", "500"]) == 0
        assert f"[{bando}]" in capsys.readouterr().out
        assert situazione.main(["--bando", str(bando)]) == 0
        assert "segnali gratuiti" in capsys.readouterr().out
    finally:
        with connetti() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM bandi WHERE id = %s", (bando,))
            conn.commit()
