"""Invio email con Resend. Senza RESEND_API_KEY il messaggio viene solo stampato (utile in prova)."""

from __future__ import annotations

import os

import httpx

MITTENTE_PREDEFINITO = "Bandi Radar <novita@finanzagevolata.qiaro.it>"


def invia(destinatario: str, oggetto: str, testo: str, html: str | None = None) -> str:
    """Ritorna 'inviata' oppure 'stampata' (nessuna chiave configurata)."""
    chiave = os.environ.get("RESEND_API_KEY")
    if not chiave:
        print(f"[email non inviata: manca RESEND_API_KEY]\nA: {destinatario}\nOggetto: {oggetto}\n\n{testo}")
        return "stampata"
    corpo = {
        "from": os.environ.get("EMAIL_MITTENTE") or MITTENTE_PREDEFINITO,
        "to": [destinatario],
        "subject": oggetto,
        "text": testo,
    }
    if html:
        corpo["html"] = html
    risposta = httpx.post("https://api.resend.com/emails", json=corpo,
                          headers={"Authorization": f"Bearer {chiave}"}, timeout=30)
    risposta.raise_for_status()
    return "inviata"
