"""Scaricamento con buone maniere: User-Agent che dice chi siamo, timeout, rispetto di robots.txt."""

from __future__ import annotations

import urllib.robotparser
from urllib.parse import urlsplit

import httpx

USER_AGENT = "BandiRadar/0.1 (+https://finanzagevolata.qiaro.it; raccolta bandi per imprese)"
TIMEOUT = 30.0

_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}


class NonPermesso(Exception):
    """robots.txt del sito vieta la pagina."""


def nuovo_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept-Language": "it"},
        follow_redirects=True,
        timeout=TIMEOUT,
    )


def permesso_da_robots(client: httpx.Client, url: str) -> bool:
    """Legge (una volta per sito) robots.txt e dice se possiamo scaricare l'indirizzo."""
    parti = urlsplit(url)
    base = f"{parti.scheme}://{parti.netloc}"
    if base not in _robots:
        parser = urllib.robotparser.RobotFileParser()
        try:
            risposta = client.get(base + "/robots.txt")
            if risposta.status_code == 200:
                parser.parse(risposta.text.splitlines())
                _robots[base] = parser
            else:
                _robots[base] = None   # niente robots.txt: tutto permesso
        except httpx.HTTPError:
            _robots[base] = None
    parser = _robots[base]
    return True if parser is None else parser.can_fetch(USER_AGENT, url)


def scarica(client: httpx.Client, url: str, accept: str | None = None) -> httpx.Response:
    if not permesso_da_robots(client, url):
        raise NonPermesso(f"robots.txt vieta {url}")
    headers = {"Accept": accept} if accept else None
    return client.get(url, headers=headers)
