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

Revisione del 06/10 sui bandi fermati dai segnali: non contano piu' come chiusura le frasi che la *prevedono* ("sara'
possibile la chiusura anticipata", "salvo chiusura anticipata": Camere di Foggia e Maremma), i menu ("ulteriori
strumenti non piu' operativi", SIMEST), "non sia ancora stato chiuso" (il bilancio, Finlombarda) e "sospeso" (puo'
riprendere). Lo stato del portale Calabria ("Conclusione Data aggiornamento stato 16 Ott 2023") e' un'etichetta vera,
ma se un annuncio dello stesso bando e' stato pubblicato dopo la data dello stato (o dopo la fine di "in vigore dal
... al ...") puo' riguardare un'edizione precedente: diventa un dubbio e decide l'IA.

Uso:  python -m app.schede.segnali --bando 381        # i segnali di un bando
      python -m app.schede.segnali --prova            # su tutti i bandi con pagina: quanti chiusi, aperti, confronto
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
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
# "Scade 10/11/2026" (Camera della Maremma: "Aperto Scade 10/11/2026 salvo chiusura anticipata").
_DATA_CHIUSURA = re.compile(r"(?:data (?:di )?(?:chiusura|scadenza)|scadenza(?: del bando| domande)?|termine ultimo|\bscade(?: il)?)"
                            r"\s*[:\-]?\s*(?:il |ore \d{1,2}[:.]\d{2} del )?" + _DATA, re.IGNORECASE)
_STATO = re.compile(r"(?:\bstato(?: del bando| bando)?\s*[:\-]?\s*|\bbando\s+)"
                    r"(aperto|attivo|in corso|chiuso|scaduto|concluso|sospeso|esaurito)\b", re.IGNORECASE)
# Calabria Europa: "Fondo: FESR Valutazione Data aggiornamento stato 16 Lug 2026".
# E' l'etichetta dello stato della procedura (Pre-informazione, Pubblicazione, Aperto, Valutazione, Conclusione,
# Chiuso, Revocato, Sospeso), non testo di servizio: la data che segue serve a riconoscere le edizioni vecchie.
_STATO_CALABRIA = re.compile(r"\b(aperto|pubblicazione|valutazione|chiuso|conclusione|sospeso)\s+data aggiornamento stato"
                             r"(?:\s*:?\s*" + _DATA + r")?", re.IGNORECASE)
# "stato chiuso" detto di altro o negato: "nel caso in cui l'ultimo bilancio non sia ancora stato chiuso" (Finlombarda).
_STATO_NEGATO = re.compile(r"\b(non|ancora|mai|bilanci[oi]|esercizi[oi])\b[^.;:]{0,25}$", re.IGNORECASE)
# Non "esaurimento delle risorse": "fino a esaurimento delle risorse" e' la formula degli sportelli aperti (ON, Nuova Impresa).
_CHIUSURA_ANTICIPATA = re.compile(r"chiusura anticipata|(risorse|fondi) (sono |risultano )?esaurit[ei]|dotazione (finanziaria )?"
                                  r"(e' |è |risulta )?esaurita|sportello (e' |è )?chiuso|non (e' |è )?pi(u'|ù) operativ"
                                  r"|strumenti? attualmente non disponibil", re.IGNORECASE)
# La chiusura anticipata solo prevista, non avvenuta: "Al raggiungimento di richieste ... sara' possibile la chiusura
# anticipata del bando" (Camera di Foggia), "salvo chiusura anticipata per esaurimento risorse" (Camera della Maremma).
_SOLO_PREVISTA = re.compile(r"\b(salvo|possibil[ei]|eventual[ei]|in caso di|potr[aà]|riserva|prevista la|prevedere la)\b"
                            r"[^.;:]{0,30}$", re.IGNORECASE)
# Voci di menu: "Consulta qui ulteriori strumenti non piu' operativi Strumenti attualmente non disponibili" (SIMEST,
# in tutte le pagine).
_MENU = re.compile(r"strumenti non pi(u'|ù) operativ|strumenti attualmente non disponibil", re.IGNORECASE)
_RIAPERTURA = re.compile(r"riapertura|riaperto|nuova finestra|proroga", re.IGNORECASE)
# Un termine per le domande con una data futura, scritto in altro modo: "PROROGATO alle ore 13.00 del 12 ottobre 2026"
# (GAL), "entro le ore 12:00 del 28 febbraio 2027" (Lombardia), "per l'annualita' 2027, dal 2 agosto 2027 e fino al 15
# settembre 2027", "Domande dal 01/10/2026 al 16/12/2026" (Camera di Bari). Conta solo come dubbio (decide l'IA).
_TERMINE = re.compile(r"(?:\bentro\b|\bfino al|\bprorogat[oa]\b|\btermine\b|\bscade\b|\bdomande dal\b[^.;]{0,40}?\bal\b)"
                      r"(?:[^.;]|(?<=\d)\.(?=\d)){0,50}?" + _DATA, re.IGNORECASE)      # "ore 13.00" non chiude la frase
# ...ma non i termini per altro: rendicontazione, lavori, progetti, eventi.
_TERMINE_ALTRO = re.compile(r"rendicont|liquidaz|realizza|conclu|lavori|spes[ae]|progett|svolg|si terr|evento", re.IGNORECASE)
# "sospeso" non e' chiuso: lo sportello puo' riprendere (Calabria Straordinaria in campo, sospeso il 09/09/2026).
_STATI_CHIUSI = {"chiuso", "scaduto", "concluso", "esaurito", "valutazione", "conclusione"}
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


def _chiusura_anticipata(testa: str) -> str | None:
    """La prima frase di chiusura anticipata avvenuta (non solo prevista, non una voce di menu)."""
    if _RIAPERTURA.search(testa):
        return None
    for m in _CHIUSURA_ANTICIPATA.finditer(testa):
        prima = testa[max(0, m.start() - 60):m.start()]
        intorno = testa[max(0, m.start() - 30):m.end() + 5]
        if _SOLO_PREVISTA.search(prima) or _MENU.search(intorno):
            continue
        return m.group(0)
    return None


def segnali_dal_testo(testo: str, oggi: date, ultima_pubblicazione: date | None = None) -> Segnali:
    """Segnali dall'inizio del testo della pagina ufficiale. `ultima_pubblicazione` e' la data dell'annuncio piu'
    recente dello stesso bando: una chiusura con una data piu' vecchia puo' riguardare un'edizione precedente."""
    s = Segnali()
    testa = re.sub(r"\s+", " ", testo or "")[:CARATTERI_TESTA]

    def chiuso_datato(motivo: str, quando: date | None) -> None:
        if quando and ultima_pubblicazione and quando < ultima_pubblicazione:
            s.aperto.append(f"{motivo}, ma un annuncio del bando e' del {ultima_pubblicazione:%d/%m/%Y} "
                            "(forse un'edizione nuova)")
        else:
            s.chiuso.append(motivo)

    for m in _IN_VIGORE.finditer(testa):
        fine = _data(m.group(2))
        if fine and fine < oggi:
            chiuso_datato(f"in vigore fino al {fine:%d/%m/%Y}", fine)
        elif fine:
            s.aperto.append(f"in vigore fino al {fine:%d/%m/%Y}")
    for m in _DATA_CHIUSURA.finditer(testa):
        fine = _data(m.group(1))
        if fine and fine >= oggi:
            s.aperto.append(f"scadenza {fine:%d/%m/%Y} scritta nella pagina")
    if not s.aperto:
        for m in _TERMINE.finditer(testa):
            fine = _data(m.group(1))
            if fine and fine >= oggi and not _TERMINE_ALTRO.search(testa[max(0, m.start() - 40):m.end()]):
                s.aperto.append(f"termine {fine:%d/%m/%Y} scritto nella pagina ('{m.group(0)[:60]}')")
                break
    for m in _STATO.finditer(testa):
        parola = m.group(1).lower()
        if parola in _STATI_CHIUSI and not _STATO_NEGATO.search(testa[max(0, m.start() - 40):m.start()]):
            s.chiuso.append(f"'{m.group(0).strip()}' nella pagina")
        elif parola in _STATI_APERTI:
            s.aperto.append(f"'{m.group(0).strip()}' nella pagina")
    for m in _STATO_CALABRIA.finditer(testa):
        parola = m.group(1).lower()
        etichetta = re.sub(r"\s*:?\s*" + _DATA + "$", "", m.group(0).strip())
        if parola in _STATI_CHIUSI:
            chiuso_datato(f"'{etichetta}' nella pagina", _data(m.group(2)) if m.group(2) else None)
        elif parola in _STATI_APERTI:
            s.aperto.append(f"'{etichetta}' nella pagina")
    frase = _chiusura_anticipata(testa)
    if frase:
        s.chiuso.append(f"'{frase}' nella pagina")
    return s


def date_barrate(html: str, oggi: date) -> list[str]:
    """Camera di Cosenza: la chiusura anticipata e' una data barrata con la nuova accanto. Ritorna i motivi di
    chiusura: la data scritta subito dopo quella barrata, se gia' passata. Solo quella subito dopo (06/10): la
    prima data del paragrafo poteva essere l'apertura ("a partire dalle ore 9:00 del 7/08/2026 e fino alle ore 12:00
    del <s>4/09/2026</s> 18/09/2026", Foggia) o la data di un avviso ("<s>dalle ore 10:00 del 01/10/2026</s> e fino
    alle ore 12:00 del 16/12/2026. AVVISO 01.01.2026", Bari)."""
    from bs4 import BeautifulSoup

    zuppa = BeautifulSoup(html, "html.parser")
    barrati = zuppa.find_all(["del", "s", "strike"]) + zuppa.find_all(style=re.compile(r"line-through", re.I))
    motivi = []
    for b in barrati:
        vecchia = re.search(_DATA, b.get_text(" "))
        if not vecchia:
            continue
        contenitore = b.find_parent(["td", "p", "li", "div"]) or b.parent
        testo, barrato = contenitore.get_text(" "), b.get_text(" ")
        dove = testo.find(barrato)
        if dove < 0:
            continue
        m = re.search(_DATA, testo[dove + len(barrato):dove + len(barrato) + 50])
        nuova = _data(m.group(1)) if m else None
        if nuova and nuova < oggi:
            motivi.append(f"data barrata {vecchia.group(1)}, nuova data {nuova:%d/%m/%Y} gia' passata")
    return motivi


def _giorno(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return _data(str(v))


def segnali_da_dati(url: str | None, annunci: list[dict], pagine: list[dict], oggi: date,
                    cartella: Path | None = None) -> Segnali:
    """I segnali da quello che si sa del bando: annunci (url, dati, pubblicato_il, ruolo), pagine ufficiali
    salvate (testo_estratto, percorso_locale). Senza database: la usa anche la prova sui dati esportati."""
    s = Segnali()
    scadenze = [d for a in annunci if (d := scadenza_nei_dati(a.get("dati") if isinstance(a.get("dati"), dict) else None))]
    if scadenze:
        s.scadenza_fonte = max(scadenze)
        if s.scadenza_fonte < oggi:
            s.chiuso.append(f"scadenza {s.scadenza_fonte:%d/%m/%Y} nei dati della fonte")
        else:
            s.aperto.append(f"scadenza {s.scadenza_fonte:%d/%m/%Y} nei dati della fonte")
    for u in ([url] if url else []) + [a.get("url") for a in annunci]:
        if _URL_CHIUSO.search(u or ""):
            s.chiuso.append(f"indirizzo tra i bandi chiusi ({u})")
            break
    # Le graduatorie, le FAQ e gli avvisi di chiusura escono dopo la chiusura: non dicono che c'e' un'edizione nuova.
    pubblicazioni = [d for a in annunci if a.get("ruolo") not in ("graduatoria", "faq", "chiusura")
                     and (d := _giorno(a.get("pubblicato_il")))]
    ultima = max(pubblicazioni, default=None)
    for p in pagine:
        dal_testo = segnali_dal_testo(p.get("testo_estratto") or "", oggi, ultima)
        s.chiuso += dal_testo.chiuso
        s.aperto += dal_testo.aperto
        if p.get("percorso_locale") and cartella:
            try:
                html = (cartella / p["percorso_locale"]).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            s.chiuso += date_barrate(html, oggi)
    return s


def segnali_del_bando(conn, bando_id: int, oggi: date | None = None, cartella: Path | None = None) -> Segnali:
    """Tutti i segnali gratuiti di un bando: dati grezzi degli annunci, indirizzi, pagina ufficiale salvata."""
    from app.schede.allegati import CARTELLA

    with conn.cursor() as cur:
        cur.execute("SELECT url FROM bandi WHERE id = %s", (bando_id,))
        riga = cur.fetchone()
        cur.execute("SELECT url, dati, pubblicato_il, ruolo FROM annunci WHERE bando_id = %s", (bando_id,))
        annunci = [dict(a) for a in cur.fetchall()]
        cur.execute("""SELECT testo_estratto, percorso_locale FROM allegati
                       WHERE bando_id = %s AND annuncio_id IS NULL AND tipo = 'pagina' AND errore IS NULL""", (bando_id,))
        pagine = [dict(p) for p in cur.fetchall()]
    return segnali_da_dati(riga["url"] if riga else None, annunci, pagine, oggi or date.today(), cartella or CARTELLA)


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
