"""Utenti e accesso: password, sessioni, ruoli, limite ai tentativi, inviti (quasi tutto con un Postgres di prova)."""

import os
import uuid

import pytest

from app import utenti as u

db = pytest.mark.skipif(not os.environ.get("PGHOST"), reason="serve un database Postgres di prova (PGHOST)")


def test_password_con_scrypt():
    h = u.hash_password("una password lunga")
    assert h.startswith("scrypt$") and "una password" not in h
    assert u.verifica_password("una password lunga", h)
    assert not u.verifica_password("un'altra password", h)
    assert not u.verifica_password("x", None) and not u.verifica_password("x", "rotto")
    assert u.hash_password("stessa") != u.hash_password("stessa")   # sale diverso ogni volta
    with pytest.raises(u.ErroreUtenti):
        u.controlla_password("corta")


def _email(nome="utente"):
    return f"{nome}-{uuid.uuid4().hex[:8]}@esempio.it"


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni
    from app.main import app

    monkeypatch.setenv("COOKIE_SICURO", "0")
    monkeypatch.setattr(u, "manda", lambda *a, **k: "stampata")
    with connetti() as conn:
        applica_migrazioni(conn)
    return TestClient(app)


def _crea(ruolo, password="password-di-prova", email=None):
    from app.db.connessione import connetti

    email = email or _email(ruolo)
    with connetti() as conn:
        u.crea_utente(conn, email, ruolo, password=password)
        conn.commit()
    return email


@db
def test_accesso_e_uscita(client):
    email = _crea("admin")
    assert client.get("/api/fonti").status_code == 401
    assert client.get("/api/accesso/io").status_code == 401
    r = client.post("/api/accesso/entra", json={"email": email.upper(), "password": "password-di-prova"})
    assert r.status_code == 200 and r.json()["ruolo"] == "admin" and "password_hash" not in r.json()
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    assert client.get("/api/accesso/io").json()["email"] == email
    assert client.get("/api/fonti").status_code == 200
    assert client.post("/api/accesso/esci").status_code == 200
    client.cookies.clear()
    assert client.get("/api/fonti").status_code == 401


@db
def test_cookie_sicuro_in_produzione(client, monkeypatch):
    monkeypatch.setenv("COOKIE_SICURO", "1")
    email = _crea("revisore")
    r = client.post("/api/accesso/entra", json={"email": email, "password": "password-di-prova"})
    assert "Secure" in r.headers["set-cookie"]


@db
def test_ruoli_revisore_e_impresa(client):
    from conftest import accesso_di_prova

    rev = accesso_di_prova("revisore")
    assert client.get("/api/bandi", auth=rev).status_code == 200
    assert client.get("/api/valori", auth=rev).status_code == 200
    assert client.get("/api/bandi/999999999", auth=rev).status_code == 404   # passa il controllo, bando inesistente
    for rotta in ("/api/fonti", "/api/annunci", "/api/profili", "/api/sistemi", "/api/lavorazione", "/api/utenti"):
        assert client.get(rotta, auth=rev).status_code == 403, rotta
    assert client.post("/api/fonti/x/pausa", json={"in_pausa": True}, auth=rev).status_code == 403
    assert client.post("/api/fonti/x/rilancia", auth=rev).status_code == 403
    imp = accesso_di_prova("impresa")
    assert client.get("/api/accesso/io", auth=imp).json()["ruolo"] == "impresa"
    for rotta in ("/api/bandi", "/api/fonti", "/api/utenti"):
        assert client.get(rotta, auth=imp).status_code == 403, rotta


@db
def test_cinque_errori_bloccano_per_quindici_minuti(client):
    email = _crea("revisore")
    for _ in range(5):
        r = client.post("/api/accesso/entra", json={"email": email, "password": "sbagliata!!"})
        assert r.status_code == 401
    r = client.post("/api/accesso/entra", json={"email": email, "password": "password-di-prova"})
    assert r.status_code == 429 and "15 minuti" in r.json()["detail"]
    # Gli errori su un indirizzo inesistente non dicono se l'utente esiste: stesso messaggio.
    r = client.post("/api/accesso/entra", json={"email": _email("nessuno"), "password": "x"})
    assert r.status_code == 401 and r.json()["detail"] == "Email o password non corretti."


@db
def test_utente_disattivato_non_entra_e_perde_la_sessione(client):
    from conftest import accesso_di_prova

    from app.db.connessione import connetti

    rev = accesso_di_prova("revisore")
    io = client.get("/api/accesso/io", auth=rev).json()
    admin = accesso_di_prova("admin")
    assert client.patch(f"/api/utenti/{io['id']}", json={"attivo": False}, auth=admin).status_code == 200
    assert client.get("/api/accesso/io", auth=rev).status_code == 401
    with connetti() as conn:
        with pytest.raises(u.ErroreUtenti):
            u.accedi(conn, io["email"], "password-di-prova")


@db
def test_invito_e_scelta_della_password(client):
    from conftest import accesso_di_prova

    admin = accesso_di_prova("admin")
    email = _email("amico")
    r = client.post("/api/utenti", json={"email": email, "nome": "Amico", "ruolo": "revisore"}, auth=admin)
    assert r.status_code == 200 and r.json()["email"] == "stampata"
    codice = r.json()["link"].split("codice=")[1]
    assert client.post("/api/utenti", json={"email": email, "ruolo": "revisore"}, auth=admin).status_code == 422
    assert client.get(f"/api/accesso/link?codice={codice}").json()["email"] == email
    assert client.post("/api/accesso/imposta-password", json={"codice": codice, "password": "corta"}).status_code == 422
    r = client.post("/api/accesso/imposta-password", json={"codice": codice, "password": "nuova-password-lunga"})
    assert r.status_code == 200 and r.json()["ruolo"] == "revisore"
    assert client.get("/api/bandi").status_code == 200            # dopo la password e' gia' dentro
    # Il link vale una volta sola.
    assert client.post("/api/accesso/imposta-password",
                       json={"codice": codice, "password": "altra-password-lunga"}).status_code == 422
    elenco = client.get("/api/utenti", auth=admin).json()
    assert any(x["email"] == email and x["password_impostata"] for x in elenco)


@db
def test_recupero_password_non_rivela_chi_esiste(client, monkeypatch):
    mandate = []
    monkeypatch.setattr(u, "manda", lambda dest, oggetto, testo: mandate.append((dest, testo)) or "stampata")
    email = _crea("revisore")
    r1 = client.post("/api/accesso/recupero", json={"email": email})
    r2 = client.post("/api/accesso/recupero", json={"email": _email("nessuno")})
    assert r1.json() == r2.json()
    assert len(mandate) == 1 and mandate[0][0] == email
    codice = mandate[0][1].split("codice=")[1].split()[0]
    assert client.post("/api/accesso/imposta-password",
                       json={"codice": codice, "password": "password-cambiata"}).status_code == 200
    r = client.post("/api/accesso/entra", json={"email": email, "password": "password-cambiata"})
    assert r.status_code == 200


@db
def test_resta_almeno_un_admin(client):
    from app.db.connessione import connetti

    with connetti() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM utenti WHERE ruolo = 'admin' AND attivo")
            admin = [r["id"] for r in cur.fetchall()]
        with pytest.raises(u.ErroreUtenti):
            for i in admin:
                u.modifica(conn, i, attivo=False)
        conn.rollback()


@db
def test_primo_admin_dal_env(client, monkeypatch):
    from app.db.connessione import connetti

    monkeypatch.setenv("BASIC_AUTH_USER", "Matteo")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "password-del-env")
    with connetti() as conn:
        # Con un admin gia' attivo il .env non serve piu'.
        _crea("admin")
        with pytest.raises(u.ErroreUtenti):
            u.accedi(conn, "matteo", "password-del-env")
        conn.commit()
        with conn.cursor() as cur:   # senza admin (dentro una transazione annullata alla fine) diventa il primo admin
            cur.execute("UPDATE utenti SET attivo = false WHERE ruolo = 'admin'")
            cur.execute("DELETE FROM utenti WHERE lower(email) = 'matteo'")
        utente, _ = u.accedi(conn, "Matteo", "password-del-env")
        assert utente["ruolo"] == "admin" and utente["email"] == "matteo"
        conn.rollback()


@db
def test_comando_crea_stampa_il_link(client, capsys):
    from app.utenti.__main__ import main

    email = _email("cli")
    assert main(["crea", "--email", email, "--ruolo", "revisore", "--nome", "Amico", "--senza-email"]) == 0
    assert "codice=" in capsys.readouterr().out
    assert main(["crea", "--email", email, "--ruolo", "revisore", "--senza-email"]) == 1
    assert main(["link", "--email", email]) == 0
    assert main(["disattiva", "--email", email]) == 0
    assert main(["elenco"]) == 0
    assert email in capsys.readouterr().out


@db
def test_permessi_del_revisore(client):
    from conftest import accesso_di_prova

    rev = accesso_di_prova("revisore")
    io = client.get("/api/accesso/io", auth=rev).json()
    assert sorted(io["permessi"]) == ["catalogo", "giudizi"]
    admin = accesso_di_prova("admin")
    assert client.get("/api/utenti/permessi", auth=admin).json()["lavoro"]
    assert client.get("/api/utenti/permessi", auth=rev).status_code == 403
    assert client.patch(f"/api/utenti/{io['id']}", json={"permessi": ["inventato"]}, auth=admin).status_code == 422
    # "Vede tutto in sola lettura": lavoro senza modifiche (il cambio fa rientrare: nuova sessione).
    assert client.patch(f"/api/utenti/{io['id']}", json={"permessi": ["catalogo", "giudizi", "lavoro"]}, auth=admin).status_code == 200
    assert client.get("/api/fonti", auth=rev).status_code == 401
    from app import utenti as u
    from app.db.connessione import connetti
    from conftest import CookieSessione

    with connetti() as conn:
        _, codice = u.accedi(conn, io["email"], "password-di-prova")
        conn.commit()
    rev = CookieSessione(codice)
    assert client.get("/api/accesso/io", auth=rev).json()["permessi"] == ["catalogo", "giudizi", "lavoro"]
    for rotta in ("/api/fonti", "/api/annunci", "/api/lavorazione", "/api/sistemi", "/api/profili", "/api/dubbi"):
        assert client.get(rotta, auth=rev).status_code == 200, rotta
    assert client.post("/api/abbina", json={"sedi": [{"provincia": "MI"}]}, auth=rev).status_code == 200   # calcolo, non modifica
    assert client.post("/api/fonti/x/pausa", json={"in_pausa": True}, auth=rev).status_code == 403
    assert client.put("/api/profili/prova-perm", json={}, auth=rev).status_code == 403
    assert client.get("/api/utenti", auth=rev).status_code == 403          # gli utenti restano dell'admin
    assert client.get("/api/imprese", auth=rev).status_code == 403         # i clienti solo con "imprese"
    assert "totale" in client.get("/api/feedback", auth=rev).json()
    assert client.patch("/api/feedback/999999", json={"stato": "respinto"}, auth=rev).status_code == 403
