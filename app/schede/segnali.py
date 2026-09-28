"""Segnali di stato gratuiti: aperto o chiuso, senza IA, da quello che Bandi Radar sa gia' di un bando.

La valutazione del 27/09 ha visto il controllo preliminare far passare bandi chiusi che si potevano fermare con
un'occhiata: la scadenza nei dati della fonte (API dei siti, catalogo incentivi.gov.it, Portale UE), "Bando
Chiuso" o "Stato: Valutazione" in testa alla pagina, "In vigore dal ... al ..." (Finpiemonte), l'indirizzo in
una cartella "bandi-chiusi" (Camera dell'Emilia), la data di chiusura barrata con la nuova accanto (Camera di
Cosenza). Qui si raccolgono questi segnali:

  - prima dell'IA: un bando con soli segnali di chiusura non va al controllo preliminare (niente spesa);
  - dopo l'IA: un bando che l'IA dice chiuso ma che ha una scadenza futura nei dati della fonte si rilegge.

Le etichette "aperto" dei siti non bastano a dire che un bando e' aperto (restano dopo la scadenza: Caserta,
Cagliari, Como-Lecco): contano solo come dubbio, cioe' impediscono di fermare il bando senza l'IA.

Uso:  python -m app.schede.segnali --bando 381        # i segnali di un bando
      python -m app.schede.segnali --prova            # su tutti i bandi con pagina: quanti chiusi, aperti, confronto
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from app.raccolta.date import leggi_data

# Campi dei dati grezzi degli annunci che contengono una scadenza (gli stessi della plancia, SCADENZA_SQL).
CAMPI_SCADENZA = ("scadenza", "data_chiusura", "dataScadenza", "deadlineDate", "publish_down", "chiusura_adesione",
                  "news_end_date", "scadenza_bando", "data_scadenza", "expires", "attributes.data_scadenza")
CARATTERI_TESTA = 2500      # si guarda solo l'inizio della pagina: in fondo ci sono menu e altri bandi

# "archivio-bandi" no: la Camera di Vicenza tiene li' anche i bandi aperti.
_URL_CHIUSO = re.compile(r"bandi[-_]?(chiusi|scaduti)", re.IGNORECASE)
_DATA = r"(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{1,2}\s+[a-z]+\s+\d{4})"
_IN_VIGORE = re.compile(r"in vigore dal\s+" + _DATA + r"\s+al\s+" + _DATA, re.IGNORECASE)
_DATA_CHIUSURA = re.compile(r"(?:data (?:di )?(?:chiusura|scadenza)|scadenza(?: del bando| domande)?|termine ultimo)"
                            r"\s*[:\-]?\s*(?:il |ore \d{1,2}[:.]\d{2} del )?" + _DATA, re.IGNORECASE)
_STATO = re.compile(r"(?:\bstato(?: del bando| bando)?\s*[:\-]?\s*|\bbando\s+)"
                    r"(aperto|attivo|in corso|chiuso|scaduto|concluso|sospeso|esaurito)\b", re.IGNORECASE)
# Calabria Europa: "Fondo: FESR Valutazione Data aggiornamento stato 16 Lug 2026".
_STATO_CALABRIA = re.compile(r"\b(aperto|pubblicazione|valutazione|chiuso|conclusione|sospeso)\s+data aggiornamento stato",
                             re.IGNORECASE)
# Non "esaurimento delle risorse": "fino a esaurimento delle risorse" e' la formula degli sportelli aperti (ON, Nuova Impresa).
_CHIUSURA_ANTICIPATA = re.compile(r"chiusura anticipata|(risorse|fondi) (sono |risultano )?esaurit[ei]|dotazione (finanziaria )?"
                                  r"(e' |è |risulta )?esaurita|sportello (e' |è )?chiuso|non (e' |è )?pi(u'|ù) operativ"
                                  r"|strumenti? attualmente non disponibil", re.IGNORECASE)
_RIAPERTURA = re.compile(r"riapertura|riaperto|nuova finestra|proroga", re.IGNORECASE)
_STATI_CHIUSI = {"chiuso", "scaduto", "concluso", "sospeso", "esaurito", "valutazione", "conclusione"}
_STATI_APERTI = {"aperto", "attivo", "in corso", "pubblicazione"}


@dataclass
class Segnali:
    chiuso: list[str] = field(default_factory=list)    # motivi che dicono "chiuso"
    aperto: list[str] = field(default_factory=list)    # motivi che dicono "aperto" (o almeno "non fermarlo senza IA")
    scadenza_fonte: date | None = None                  # la scadenza piu' lontana scritta nei dati della fonte

    @property
    def stato(self) -> str | None:
        """'chiuso' solo con segnali di chiusura e nessun segnale contrario; 'aperto' al contrario; altrimenti None."""
        if self.chiuso and not self.aperto:
            return "chiuso"
        if self.aperto and not self.chiuso:
            return "aperto"
        return None

    @property
    def scadenza_futura(self) -> bool:
        return self.scadenza_fonte is not None and self.scadenza_fonte >= date.today()

    def descrivi(self) -> str:
        parti = [f"chiuso: {'; '.join(self.chiuso)}" if self.chiuso else "", f"aperto: {'; '.join(self.aperto)}" if self.aperto else ""]
        return " | ".join(p for p in parti if p) or "nessun segnale"


def _valore(dati: dict, percorso: str):
    v = dati
    for parte in percorso.split("."):
        if not isinstance(v, dict):
            return None
        v = v.get(parte)
    return v


def scadenza_nei_dati(dati: dict | None) -> date | None:
    """La scadenza piu' lontana tra i campi noti dei dati grezzi di un annuncio."""
    trovate = []
    for campo in CAMPI_SCADENZA:
        v = _valore(dati or {}, campo)
        for x in v if isinstance(v, list) else [v]:
            d = leggi_data(str(x)) if x not in (None, "") else None
            if d is not None:
                trovate.append(d.date())
    return max(trovate, default=None)


def _data(testo: str) -> date | None:
    d = leggi_data(testo)
    return d.date() if d else None


def segnali_dal_testo(testo: str, oggi: date) -> Segnali:
    """Segnali dall'inizio del testo della pagina ufficiale."""
    s = Segnali()
    testa = re.sub(r"\s+", " ", testo or "")[:CARATTERI_TESTA]
    for m in _IN_VIGORE.finditer(testa):
        fine = _data(m.group(2))
        if fine:
            (s.chiuso if fine < oggi else s.aperto).append(f"in vigore fino al {fine:%d/%m/%Y}")
    for m in _DATA_CHIUSURA.finditer(testa):
        fine = _data(m.group(1))
        if fine and fine >= oggi:
            s.aperto.append(f"scadenza {fine:%d/%m/%Y} scritta nella pagina")
    for m in list(_STATO.finditer(testa)) + list(_STATO_CALABRIA.finditer(testa)):
        parola = m.group(1).lower()
        if parola in _STATI_CHIUSI:
            s.chiuso.append(f"'{m.group(0).strip()}' nella pagina")
        elif parola in _STATI_APERTI:
            s.aperto.append(f"'{m.group(0).strip()}' nella pagina")
    m = _CHIUSURA_ANTICIPATA.search(testa)
    if m and not _RIAPERTURA.search(testa):
        s.chiuso.append(f"'{m.group(0)}' nella pagina")
    return s


def date_barrate(html: str, oggi: date) -> list[str]:
    """Camera di Cosenza: la chiusura anticipata e' una data barrata con la nuova accanto. Ritorna i motivi di
    chiusura: date non barrate, vicine a una barrata, gia' passate."""
    from bs4 import BeautifulSoup

    zuppa = BeautifulSoup(html, "html.parser")
    barrati = zuppa.find_all(["del", "s", "strike"]) + zuppa.find_all(style=re.compile(r"line-through", re.I))
    motivi = []
    for b in barrati:
        vecchia = re.search(_DATA, b.get_text(" "))
        if not vecchia:
            continue
        contenitore = b.find_parent(["td", "p", "li", "div"]) or b.parent
        resto = contenitore.get_text(" ").replace(b.get_text(" "), " ")
        for m in re.finditer(_DATA, resto):
            nuova = _data(m.group(1))
            if nuova and nuova < oggi:
                motivi.append(f"data barrata {vecchia.group(1)}, nuova data {nuova:%d/%m/%Y} gia' passata")
                break
    return motivi


def segnali_del_bando(conn, bando_id: int, oggi: date | None = None, cartella: Path | None = None) -> Segnali:
    """Tutti i segnali gratuiti di un bando: dati grezzi degli annunci, indirizzi, pagina ufficiale salvata."""
    from app.schede.allegati import CARTELLA

    oggi = oggi or date.today()
    cartella = cartella or CARTELLA
    s = Segnali()
    with conn.cursor() as cur:
        cur.execute("SELECT url FROM bandi WHERE id = %s", (bando_id,))
        riga = cur.fetchone()
        indirizzi = [riga["url"]] if riga and riga["url"] else []
        cur.execute("SELECT url, dati FROM annunci WHERE bando_id = %s", (bando_id,))
        annunci = cur.fetchall()
        cur.execute("""SELECT testo_estratto, percorso_locale FROM allegati
                       WHERE bando_id = %s AND annuncio_id IS NULL AND tipo = 'pagina' AND errore IS NULL""", (bando_id,))
        pagine = cur.fetchall()
    scadenze = [d for a in annunci if (d := scadenza_nei_dati(a["dati"] if isinstance(a["dati"], dict) else None))]
    if scadenze:
        s.scadenza_fonte = max(scadenze)
        if s.scadenza_fonte < oggi:
            s.chiuso.append(f"scadenza {s.scadenza_fonte:%d/%m/%Y} nei dati della fonte")
        else:
            s.aperto.append(f"scadenza {s.scadenza_fonte:%d/%m/%Y} nei dati della fonte")
    for u in indirizzi + [a["url"] for a in annunci]:
        if _URL_CHIUSO.search(u or ""):
            s.chiuso.append(f"indirizzo tra i bandi chiusi ({u})")
            break
    for p in pagine:
        dal_testo = segnali_dal_testo(p["testo_estratto"] or "", oggi)
        s.chiuso += dal_testo.chiuso
        s.aperto += dal_testo.aperto
        if p["percorso_locale"]:
            try:
                html = (cartella / p["percorso_locale"]).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            s.chiuso += date_barrate(html, oggi)
    return s


def esegui(bando_id: int | None, prova: bool) -> int:
    from collections import Counter

    from app.db.connessione import connetti

    with connetti() as conn:
        if bando_id:
            print(segnali_del_bando(conn, bando_id).descrivi())
            return 0
        with conn.cursor() as cur:
            cur.execute("""SELECT id, titolo, stato, dati IS NOT NULL AS scheda, preliminare->>'stato' AS pre
                           FROM bandi WHERE pagina_stato = 'trovata' ORDER BY id""")
            bandi = cur.fetchall()
        conti: Counter = Counter()
        esempi: dict[str, list[str]] = {}
        for b in bandi:
            s = segnali_del_bando(conn, b["id"])
            chiave = f"segnali {s.stato or 'misti/nessuno'} | stato calcolato {b['stato'] or '-'} | preliminare {b['pre'] or '-'}"
            conti[chiave] += 1
            if s.stato and len(esempi.setdefault(chiave, [])) < 4:
                esempi[chiave].append(f"   [{b['id']}] {b['titolo'][:60]} -- {s.descrivi()[:200]}")
        for chiave, n in conti.most_common():
            print(f"{n:5d}  {chiave}")
            for e in esempi.get(chiave, []):
                print(e)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Segnali di stato gratuiti dei bandi (senza IA).")
    parser.add_argument("--bando", type=int, metavar="ID")
    parser.add_argument("--prova", action="store_true", help="su tutti i bandi con pagina: conteggi ed esempi")
    args = parser.parse_args(argv)
    return esegui(args.bando, args.prova)


if __name__ == "__main__":
    sys.exit(main())
