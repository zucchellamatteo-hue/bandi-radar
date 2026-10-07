"""Invio email con Resend. Senza RESEND_API_KEY il messaggio viene solo stampato (utile in prova).

Tutte le email sono automatiche: il mittente e' "non-rispondere@" e in fondo c'e' sempre l'avviso di non rispondere
(Matteo, 05/10/2026: nessuno legge quella casella). Il dominio e' quello di SITO_URL, cosi' cambiando dominio cambia
anche il mittente.
"""

from __future__ import annotations

import html as html_mod
import os
from urllib.parse import urlparse

import httpx


def mittente() -> str:
    if os.environ.get("EMAIL_MITTENTE"):
        return os.environ["EMAIL_MITTENTE"]
    dominio = urlparse(os.environ.get("SITO_URL") or "https://finanzagevolata.qiaro.it").hostname
    return f"Bandi Radar <non-rispondere@{dominio}>"


def avviso_non_rispondere() -> str:
    contatto = os.environ.get("EMAIL_CONTATTO")
    testo = "Questa è un'email automatica: per favore non rispondere, nessuno legge questa casella."
    return testo + (f" Per qualsiasi domanda scrivi a {contatto}." if contatto else "")


def con_avviso(testo: str, html: str | None) -> tuple[str, str | None]:
    avviso = avviso_non_rispondere()
    testo = f"{testo.rstrip()}\n\n--\n{avviso}\n"
    if html:
        piede = (f'<p style="max-width:640px;margin:24px auto 0;padding-top:12px;border-top:1px solid #e2e8f0;'
                 f'color:#64748b;font-size:12px">{html_mod.escape(avviso)}</p>')
        html = html.replace("</body>", piede + "</body>") if "</body>" in html else html + piede
    return testo, html


def invia(destinatario: str, oggetto: str, testo: str, html: str | None = None) -> str:
    """Ritorna 'inviata' oppure 'stampata' (nessuna chiave configurata)."""
    testo, html = con_avviso(testo, html)
    chiave = os.environ.get("RESEND_API_KEY")
    if not chiave:
        print(f"[email non inviata: manca RESEND_API_KEY]\nA: {destinatario}\nOggetto: {oggetto}\n\n{testo}")
        return "stampata"
    corpo = {"from": mittente(), "to": [destinatario], "subject": oggetto, "text": testo}
    if html:
        corpo["html"] = html
    risposta = httpx.post("https://api.resend.com/emails", json=corpo,
                          headers={"Authorization": f"Bearer {chiave}"}, timeout=30)
    risposta.raise_for_status()
    return "inviata"
