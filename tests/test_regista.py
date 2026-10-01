"""Regista della fase 2: regole dei doppioni (senza database) e un giro dei passi su un Postgres di prova vuoto."""

import os

import pytest

from app.catena import regista


def dubbio(somiglianza, ente="Camera di Commercio di Modena", ente_bando="CCIAA Modena", bando_id=7):
    return {"bando_id": bando_id, "somiglianza": somiglianza, "ente": ente, "bando_ente_fonte": ente_bando, "bando_ente": None,
            "titolo": "Voucher export 2026", "bando_titolo": "Voucher export - 2026"}


def test_regole_dei_doppioni():
    assert regista.decisione_regole(dubbio(0.95))[0] == "stesso"
    assert regista.decisione_regole(dubbio(0.95, ente_bando="Regione Lombardia")) is None   # enti diversi: l'IA
    assert regista.decisione_regole(dubbio(0.8)) is None                                   # simili: l'IA
    assert regista.decisione_regole(dubbio(0.6)) is None                                   # ente e gestore: l'IA
    assert regista.decisione_regole(dubbio(0.4))[0] == "diverso"
    edizione = {**dubbio(1.0), "titolo": "Riapri Calabria - Seconda edizione", "bando_titolo": "Riapri Calabria"}
    assert regista.decisione_regole(edizione) is None
    anni = {**dubbio(0.95), "titolo": "Voucher digitali 2026", "bando_titolo": "Voucher digitali 2025"}
    assert regista.decisione_regole(anni) is None
    assert regista.decisione_regole(dubbio(None, bando_id=None))[0] == "archivia"           # graduatoria orfana


@pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")
def test_giro_dei_passi_sul_database():
    from app.catena import stato
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM annunci WHERE NOT starts_with(fonte_id, 'prova_')")
            if cur.fetchone()["n"]:
                pytest.skip("il database contiene annunci veri")
            cur.execute("""INSERT INTO fonti (id, nome, ente, tipo, territorio, modalita, frequenza, stato) VALUES
                ('prova_regista', 'Camera', 'Camera di Commercio di Modena', 'camera', 'EMR', 'html', 'settimanale', 'attiva')
                ON CONFLICT (id) DO NOTHING""")
            ids = {}
            for n, titolo in enumerate(["Voucher export 2026", "Voucher export 2026 - proroga", "Bando incerto",
                                        "Graduatoria bando sconosciuto", "Contributi fiere 2026"], start=1):
                cur.execute("""INSERT INTO annunci (fonte_id, url, titolo, impronta, trovato_il)
                               VALUES ('prova_regista', %s, %s, 'x', now()) RETURNING id""", (f"https://mo.camcom.it/{n}", titolo))
                ids[n] = cur.fetchone()["id"]
            cur.execute("""INSERT INTO bandi (annuncio_id, titolo, ente, url, dati, completezza, scheda_il)
                           VALUES (%s, 'Voucher export 2026', 'Camera di Commercio di Modena', 'https://mo.camcom.it/1',
                                   '{}', 'bando_ufficiale', now() - interval '1 day') RETURNING id""", (ids[1],))
            bando = cur.fetchone()["id"]
            cur.execute("UPDATE annunci SET bando_id = %s, ruolo = 'origine', collegato_da = 'regole' WHERE id = %s", (bando, ids[1]))
            for n, esito, da in [(1, "rilevante", "regole"), (2, "rilevante", "regole"), (3, "da_rivedere", "ia"),
                                 (4, "rilevante", "regole"), (5, "rilevante", "regole")]:
                cur.execute("INSERT INTO smistamenti (annuncio_id, esito, deciso_da) VALUES (%s, %s, %s)", (ids[n], esito, da))
            cur.execute("""INSERT INTO bandi_dubbi (annuncio_id, bando_id, somiglianza, motivo) VALUES
                           (%s, %s, 0.93, 'titolo simile'), (%s, NULL, NULL, 'graduatoria: non trovo il bando'),
                           (%s, %s, 0.4, 'titolo poco simile')""", (ids[2], bando, ids[4], ids[5], bando))
        conn.commit()
        try:
            assert regista.ripiego_da_rivedere(conn) == 1
            conteggi = regista.sblocca_dubbi(conn, usa_ia=False)
            assert (conteggi["stesso"], conteggi["archivia"], conteggi["diverso"]) == (1, 1, 1)
            with conn.cursor() as cur:
                cur.execute("SELECT id, bando_id FROM annunci WHERE fonte_id = 'prova_regista'")
                legami = {r["id"]: r["bando_id"] for r in cur.fetchall()}
                cur.execute("SELECT esito FROM smistamenti WHERE annuncio_id = %s", (ids[4],))
                archiviato = cur.fetchone()["esito"]
                cur.execute("SELECT esito, proposta_da FROM smistamenti WHERE annuncio_id = %s", (ids[3],))
                incerto = cur.fetchone()
            assert legami[ids[2]] == bando                      # proroga unita al bando
            assert legami[ids[5]] not in (None, bando)          # bando nuovo
            assert archiviato == "non_rilevante"
            assert incerto["esito"] == "rilevante" and incerto["proposta_da"] == "ia"
            # La proroga e' arrivata dopo la scheda: la scheda va aggiornata, senza creare una nuova versione.
            with conn.cursor() as cur:
                cur.execute("UPDATE annunci SET ruolo = 'proroga', collegato_il = now() WHERE id = %s", (ids[2],))
                cur.execute("SELECT versione FROM bandi WHERE id = %s", (bando,))
                versione = cur.fetchone()["versione"]
            conn.commit()
            assert regista.segna_aggiornamenti(conn) == 1
            with conn.cursor() as cur:
                cur.execute("SELECT da_aggiornare, versione FROM bandi WHERE id = %s", (bando,))
                riga = cur.fetchone()
            assert "proroga" in riga["da_aggiornare"] and riga["versione"] == versione
            imbuto = stato.imbuto(conn)
            assert {f["fase"]: f["n"] for f in imbuto["bandi"]}["scheda_da_aggiornare"] >= 1
            assert any(e["passo"] == "doppione" for e in imbuto["eventi"])
            assert stato.elenco(conn, "bandi", "scheda_da_aggiornare")[0]["motivo"].startswith("proroga")
        finally:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM annunci WHERE fonte_id = 'prova_regista'")
                annunci = [r["id"] for r in cur.fetchall()]
                cur.execute("SELECT DISTINCT bando_id FROM annunci WHERE id = ANY(%s) AND bando_id IS NOT NULL", (annunci,))
                bandi = [r["bando_id"] for r in cur.fetchall()] + [bando]
                cur.execute("DELETE FROM eventi_catena WHERE oggetto_id = ANY(%s) OR oggetto_id = ANY(%s)", (annunci, bandi))
                cur.execute("DELETE FROM bandi_dubbi WHERE annuncio_id = ANY(%s)", (annunci,))
                cur.execute("DELETE FROM smistamenti WHERE annuncio_id = ANY(%s)", (annunci,))
                cur.execute("UPDATE annunci SET bando_id = NULL WHERE id = ANY(%s)", (annunci,))
                cur.execute("DELETE FROM bandi WHERE id = ANY(%s)", (bandi,))
                cur.execute("DELETE FROM annunci WHERE id = ANY(%s)", (annunci,))
                cur.execute("DELETE FROM fonti WHERE id = 'prova_regista'")
            conn.commit()
