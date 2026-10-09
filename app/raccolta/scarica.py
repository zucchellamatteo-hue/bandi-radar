"""Scaricamento con buone maniere: User-Agent che dice chi siamo, timeout, rispetto di robots.txt."""

from __future__ import annotations

import ssl
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import certifi
import httpx

from app.raccolta.robots import Regole, analizza, permesso

USER_AGENT = "BandiRadar/0.1 (+https://finanzagevolata.qiaro.it; raccolta bandi per imprese)"
TIMEOUT = 30.0

_robots: dict[str, Regole] = {}

# Certificati intermedi pubblici che alcuni siti non mandano (09/10/2026, prossimo passo 38): MIT e ISMEA (Sectigo
# Public Server Authentication CA DV R36) ed ENEA (HARICA GEANT TLS RSA 1). I browser li recuperano da soli dall'AIA
# del certificato, Python no: senza questi la verifica fallisce con "unable to get local issuer certificate". Sono
# certificati di autorita' pubbliche, presi dagli indirizzi AIA dei siti; la verifica resta completa fino alla radice.
INTERMEDI = Path(__file__).with_name("certificati_intermedi.pem")


@lru_cache(maxsize=1)
def contesto_ssl() -> ssl.SSLContext:
    """Le autorita' di certifi piu' gli intermedi mancanti di alcuni siti pubblici."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    if INTERMEDI.is_file():
        ctx.load_verify_locations(cafile=str(INTERMEDI))
    return ctx


class NonPermesso(Exception):
    """robots.txt del sito vieta la pagina."""


def nuovo_client(ipv6: bool = False) -> httpx.Client:
    """Con ipv6=True la connessione esce solo in IPv6: alcuni siti (Napoli, Siracusa) rifiutano l'IPv4 del server
    ma accettano l'IPv6. Richiede che il container abbia l'IPv6 (rete `ipv6` in docker-compose.yml)."""
    return httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "it"},
        follow_redirects=True,
        timeout=TIMEOUT,
        transport=httpx.HTTPTransport(local_address="::", verify=contesto_ssl()) if ipv6 else None,
        verify=contesto_ssl(),
    )


def regole_robots(client: httpx.Client, url: str) -> Regole:
    """Legge (una volta per sito) robots.txt. Senza file, o con errore, tutto e' permesso."""
    parti = urlsplit(url)
    base = f"{parti.scheme}://{parti.netloc}"
    if base not in _robots:
        try:
            risposta = client.get(base + "/robots.txt")
            _robots[base] = analizza(risposta.text, USER_AGENT) if risposta.status_code == 200 else Regole()
        except httpx.HTTPError:
            _robots[base] = Regole()
    return _robots[base]


def scarica(client: httpx.Client, url: str, accept: str | None = None, ignora_robots: bool = False) -> httpx.Response:
    if not ignora_robots and not permesso(regole_robots(client, url), url):
        raise NonPermesso(f"robots.txt vieta {url}")
    headers = {"Accept": accept} if accept else None
    return client.get(url, headers=headers)
