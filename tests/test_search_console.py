"""Search Console nel rapporto SEO/GEO (09/10/2026): chiave dal .env, JWT firmato, risposte di Google finte (nessuna
chiamata vera), righe del rapporto."""

import base64
import json
from datetime import date

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.notifiche import rapporto_seo
from app.pubblico import search_console as sc


def _chiave(monkeypatch):
    privata = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = privata.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    cred = {"client_email": "lettore@progetto.iam.gserviceaccount.com", "private_key": pem,
            "token_uri": "https://oauth2.googleapis.com/token"}
    monkeypatch.setenv("GSC_CHIAVE_JSON_B64", base64.b64encode(json.dumps(cred).encode()).decode())
    sc._token.clear()
    return privata, cred


def test_senza_chiave_niente(monkeypatch):
    monkeypatch.delenv("GSC_CHIAVE_JSON_B64", raising=False)
    assert sc.credenziali() is None and sc.dati() is None
    monkeypatch.setenv("GSC_CHIAVE_JSON_B64", "non-e-base64-json")
    assert sc.credenziali() is None
    assert rapporto_seo.righe_search_console(None)[0].startswith("Search Console: non ancora collegato.")


def test_jwt_firmato_e_verificabile(monkeypatch):
    privata, cred = _chiave(monkeypatch)
    testa, corpo, firma = sc.jwt_firmato(cred, adesso=1_000).split(".")
    pad = lambda x: x + "=" * (-len(x) % 4)  # noqa: E731
    dati = json.loads(base64.urlsafe_b64decode(pad(corpo)))
    assert dati["iss"] == cred["client_email"] and dati["scope"].endswith("webmasters.readonly") and dati["exp"] == 4_600
    privata.public_key().verify(base64.urlsafe_b64decode(pad(firma)), f"{testa}.{corpo}".encode(),
                                padding.PKCS1v15(), hashes.SHA256())


def test_dati_con_risposte_finte(monkeypatch):
    _chiave(monkeypatch)
    monkeypatch.setenv("GSC_PROPRIETA", "sc-domain:bandinqiaro.it")
    chiamate = []

    def risponde(req: httpx.Request) -> httpx.Response:
        chiamate.append(req)
        if "oauth2" in str(req.url):
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})
        corpo = json.loads(req.content)
        assert req.headers["Authorization"] == "Bearer tok" and "sc-domain%3Abandinqiaro.it" in str(req.url)
        assert corpo["startDate"] == "2026-09-30" and corpo["endDate"] == "2026-10-06"     # 7 giorni, fino a 3 giorni fa
        if not corpo["dimensions"]:
            return httpx.Response(200, json={"rows": [{"clicks": 4, "impressions": 250, "ctr": 0.016, "position": 18.44}]})
        return httpx.Response(200, json={"rows": [{"keys": ["iperammortamento 2026"], "clicks": 3, "impressions": 120,
                                                   "position": 12.27}]})

    d = sc.dati(oggi=date(2026, 10, 9), client=httpx.Client(transport=httpx.MockTransport(risponde)))
    assert d["impressioni"] == 250 and d["clic"] == 4 and d["ctr"] == 1.6 and d["posizione"] == 18.4
    assert d["query"] == [("iperammortamento 2026", 3, 120, 12.3)]
    assert len(chiamate) == 4                                                              # token + 3 interrogazioni
    righe = rapporto_seo.righe_search_console(d)
    assert "250 impressioni, 4 clic" in righe[0] and "dal 30/09 al 06/10" in righe[0]
    assert "iperammortamento 2026 (3 clic, 120 impressioni, pos. 12.3)" in righe[1]


def test_errore_di_google_non_ferma_il_rapporto(monkeypatch):
    _chiave(monkeypatch)
    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(403, json={"error": "no"})))
    d = sc.dati(oggi=date(2026, 10, 9), client=client)
    assert "errore" in d and "HTTPStatusError" in d["errore"]
    assert rapporto_seo.righe_search_console(d)[0].startswith("Search Console: Search Console non ha risposto")
