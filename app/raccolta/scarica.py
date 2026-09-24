"""Scaricamento con buone maniere: User-Agent che dice chi siamo, timeout, rispetto di robots.txt."""

from __future__ import annotations

from urllib.parse import urlsplit

import httpx

from app.raccolta.robots import Regole, analizza, permesso

USER_AGENT = "BandiRadar/0.1 (+https://finanzagevolata.qiaro.it; raccolta bandi per imprese)"
TIMEOUT = 30.0

_robots: dict[str, Regole] = {}


class NonPermesso(Exception):
    """robots.txt del sito vieta la pagina."""


def nuovo_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "it"},
        follow_redirects=True,
        timeout=TIMEOUT,
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
