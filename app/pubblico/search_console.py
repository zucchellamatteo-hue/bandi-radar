"""Dati di Google Search Console per il rapporto SEO/GEO (09/10/2026, PIANO_SEO_GEO punto 5).

Si legge con un "account di servizio" di Google Cloud (sola lettura) aggiunto come utente della proprieta' Search
Console. La chiave dell'account (il file JSON che Google fa scaricare) va SOLO nel .env del server, codificata in base64
su una riga: GSC_CHIAVE_JSON_B64. GSC_PROPRIETA e' la proprieta' (di base "sc-domain:bandinqiaro.it", la proprieta'
"Dominio" verificata da Matteo l'08/10). Senza chiave il rapporto dice "non ancora collegato", come prima.

Niente librerie di Google: il token si chiede con un JWT firmato RS256 (libreria cryptography), poi una chiamata a
searchAnalytics.query per i totali, le query e le pagine. I dati di Search Console arrivano con 2-3 giorni di ritardo:
il periodo si ferma a 3 giorni fa.

Prova:  python -m app.pubblico.search_console      # stampa i numeri degli ultimi 7 giorni disponibili
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from datetime import date, timedelta
from urllib.parse import quote

import httpx

AMBITO = "https://www.googleapis.com/auth/webmasters.readonly"
API = "https://www.googleapis.com/webmasters/v3/sites/{sito}/searchAnalytics/query"
RITARDO_GIORNI = 3
_token: dict = {}


def proprieta() -> str:
    return (os.environ.get("GSC_PROPRIETA") or "sc-domain:bandinqiaro.it").strip()


def credenziali() -> dict | None:
    """Il JSON dell'account di servizio dal .env, o None se non c'e' (o non e' valido)."""
    grezzo = (os.environ.get("GSC_CHIAVE_JSON_B64") or "").strip()
    if not grezzo:
        return None
    try:
        dati = json.loads(base64.b64decode(grezzo))
    except (ValueError, json.JSONDecodeError):
        return None
    return dati if dati.get("client_email") and dati.get("private_key") else None


def _b64(dati: bytes) -> str:
    return base64.urlsafe_b64encode(dati).rstrip(b"=").decode()


def jwt_firmato(cred: dict, adesso: int | None = None) -> str:
    """Il JWT per chiedere il token a Google (OAuth 2.0 per account di servizio), firmato RS256."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    adesso = adesso or int(time.time())
    testa = {"alg": "RS256", "typ": "JWT"}
    corpo = {"iss": cred["client_email"], "scope": AMBITO, "aud": cred.get("token_uri") or "https://oauth2.googleapis.com/token",
             "iat": adesso, "exp": adesso + 3600}
    firmare = f"{_b64(json.dumps(testa).encode())}.{_b64(json.dumps(corpo).encode())}"
    chiave = serialization.load_pem_private_key(cred["private_key"].encode(), password=None)
    firma = chiave.sign(firmare.encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{firmare}.{_b64(firma)}"


def _access_token(cred: dict, client: httpx.Client) -> str:
    if _token.get("valore") and _token.get("scade", 0) > time.time() + 60:
        return _token["valore"]
    r = client.post(cred.get("token_uri") or "https://oauth2.googleapis.com/token",
                    data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt_firmato(cred)})
    r.raise_for_status()
    d = r.json()
    _token.update(valore=d["access_token"], scade=time.time() + int(d.get("expires_in", 3600)))
    return d["access_token"]


def periodo(oggi: date | None = None) -> tuple[date, date]:
    """Gli ultimi 7 giorni con i dati gia' disponibili (fino a 3 giorni fa)."""
    a = (oggi or date.today()) - timedelta(days=RITARDO_GIORNI)
    return a - timedelta(days=6), a


def _interroga(client: httpx.Client, token: str, da: date, a: date, dimensioni: list[str], righe: int = 10) -> list[dict]:
    r = client.post(API.format(sito=quote(proprieta(), safe="")), headers={"Authorization": f"Bearer {token}"},
                    json={"startDate": da.isoformat(), "endDate": a.isoformat(), "dimensions": dimensioni,
                          "rowLimit": righe, "dataState": "final"})
    r.raise_for_status()
    return r.json().get("rows") or []


def dati(oggi: date | None = None, client: httpx.Client | None = None) -> dict | None:
    """{"da", "a", "impressioni", "clic", "ctr", "posizione", "query": [(testo, clic, impressioni, posizione)],
    "pagine": [...]} per gli ultimi 7 giorni disponibili; None senza chiave; {"errore": "..."} se Google non risponde."""
    cred = credenziali()
    if not cred:
        return None
    da, a = periodo(oggi)
    proprio = client is None
    client = client or httpx.Client(timeout=30)
    try:
        token = _access_token(cred, client)
        totali = _interroga(client, token, da, a, [], 1)
        query = _interroga(client, token, da, a, ["query"])
        pagine = _interroga(client, token, da, a, ["page"])
    except (httpx.HTTPError, KeyError, ValueError) as e:
        return {"errore": f"Search Console non ha risposto ({type(e).__name__}: {str(e)[:150]})"}
    finally:
        if proprio:
            client.close()
    t = totali[0] if totali else {}

    def voci(righe):
        return [(r["keys"][0], int(r.get("clicks", 0)), int(r.get("impressions", 0)), round(r.get("position", 0), 1))
                for r in righe]

    return {"da": da, "a": a, "impressioni": int(t.get("impressions", 0)), "clic": int(t.get("clicks", 0)),
            "ctr": round(100 * t.get("ctr", 0), 1), "posizione": round(t.get("position", 0), 1),
            "query": voci(query), "pagine": voci(pagine)}


def main() -> int:
    d = dati()
    if d is None:
        print("Search Console non collegata: manca GSC_CHIAVE_JSON_B64 nel .env.")
        return 1
    if "errore" in d:
        print(d["errore"])
        return 1
    print(f"{proprieta()} dal {d['da']:%d/%m} al {d['a']:%d/%m}: {d['impressioni']} impressioni, {d['clic']} clic, "
          f"CTR {d['ctr']}%, posizione media {d['posizione']}")
    for nome in ("query", "pagine"):
        print(f"== {nome}")
        for testo, clic, imp, pos in d[nome]:
            print(f"- {testo}: {clic} clic, {imp} impressioni, posizione {pos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
