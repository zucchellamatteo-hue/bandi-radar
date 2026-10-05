"""Il catalogo incentivi.gov.it non rende "nazionale" un bando locale (05/10/2026: caso del Comune di Rimini)."""

import json
import os

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_bando_comunale_ripreso_dal_catalogo_resta_locale():
    from app.abbinamento import catalogo, regole
    from app.abbinamento.profilo import Profilo
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.schede.campi import VINCOLI

    vincoli = {v: "nessun_vincolo" for v in VINCOLI}
    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            for fid, tipo, terr in (("prova_comune_rn", "capoluogo", "EMR"), ("incentivi_gov_ricerca", "nazionale", "ITA"),
                                    ("prova_ministero", "nazionale", "ITA")):
                cur.execute("INSERT INTO fonti (id, nome, ente, tipo, territorio, modalita, frequenza, stato) "
                            "VALUES (%s, %s, 'Ente', %s, %s, 'api', 'settimanale', 'attiva') ON CONFLICT (id) DO NOTHING",
                            (fid, fid, tipo, terr))
            ids = []
            for titolo, fonti in (("Eventi a Rimini", ("prova_comune_rn", "incentivi_gov_ricerca")),
                                  ("Misura del ministero", ("prova_ministero", "incentivi_gov_ricerca")),
                                  ("Solo nel catalogo", ("incentivi_gov_ricerca",))):
                cur.execute("""INSERT INTO bandi (titolo, stato, completezza, dati, vincoli) VALUES (%s, 'aperto', 'bando_ufficiale',
                               '{"risposta": {}}', %s) RETURNING id""", (titolo, json.dumps(vincoli)))
                bid = cur.fetchone()["id"]
                ids.append(bid)
                for i, f in enumerate(fonti):
                    cur.execute("INSERT INTO annunci (fonte_id, url, titolo, impronta, bando_id) VALUES (%s, %s, %s, %s, %s)",
                                (f, f"https://esempio.it/{bid}/{i}", titolo, f"imp-{bid}-{i}", bid))
        conn.commit()
        try:
            bandi = {b["id"]: b for b in catalogo.carica_bandi(conn) if b["id"] in ids}
        finally:   # niente annunci di fonti "vere" lasciati nel database di prova (li controlla test_regista)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM annunci WHERE bando_id = ANY(%s)", (ids,))
                cur.execute("DELETE FROM bandi WHERE id = ANY(%s)", (ids,))
            conn.commit()
    rimini, ministero, catalogo_solo = (bandi[i] for i in ids)
    assert rimini["livelli"] == ["capoluogo"]
    assert ministero["livelli"] == ["nazionale"] and catalogo_solo["livelli"] == ["nazionale"]
    milano = Profilo.model_validate({"codice": "x", "sedi": [{"provincia": "MI"}], "ateco": ["62.01"]}).per_regole()
    esito = regole.valuta(rimini, milano)
    assert esito.fuori_zona and esito.livello == regole.DA_VERIFICARE
    assert not regole.valuta(ministero, milano).fuori_zona
