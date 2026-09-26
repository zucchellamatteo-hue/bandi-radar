"""Deduplica senza IA: dagli annunci rilevanti ai bandi (un bando, molti annunci).

Lo stesso bando arriva da piu' fonti (catalogo incentivi.gov.it, Regione, Camera, notizia di Unioncamere) e
poi con proroghe, rettifiche, graduatorie e FAQ. Questo comando collega ogni annuncio rilevante al suo bando,
creandolo se non esiste. Le chiavi, dalla piu' affidabile:

  1. codice ufficiale del bando (Lombardia: RLO12026055023), nei dati grezzi, nell'indirizzo o nel titolo;
  2. indirizzo della pagina ripulito (anche il `link_ente` di incentivi.gov.it). Un indirizzo che nella stessa
     fonte compare in piu' annunci (una pagina elenco, un'API) non identifica un bando e non si usa;
  3. titolo: stesso ente, stessa edizione (anni, "secondo sportello") e stesse parole.

Se il titolo somiglia a quello di un bando esistente ma non e' uguale, il caso resta "dubbio" (tabella
bandi_dubbi) e l'annuncio non viene collegato: oggi decide Matteo dalla plancia, piu' avanti Haiku.
Lo stesso per proroghe, graduatorie e simili di cui non si trova il bando.
I collegamenti decisi da Matteo non vengono mai toccati.

Uso:
  python -m app.schede.bandi                 # collega gli annunci rilevanti non ancora collegati
  python -m app.schede.bandi --prova         # non scrive nulla: quanti bandi, esempi di doppioni e di dubbi
  python -m app.schede.bandi --prova --esempi 20
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit

from app.schede.smista import normalizza

# --- codici ufficiali -----------------------------------------------------------------------------

# Regione Lombardia (Bandi Online e Anagrafica dei bandi): RL + due caratteri + anno + 6 cifre.
_CODICE_LOMBARDIA = re.compile(r"(?<![A-Z0-9])(RL[A-Z][A-Z0-9]20\d{2}\d{6})(?![A-Z0-9])")
# Campi dei dati grezzi che contengono un codice ufficiale del bando (Lombardia, portale UE).
_CAMPI_CODICE = ("codice_bando", "identifier", "callIdentifier", "topicIdentifier")


def codice_ufficiale(url: str, titolo: str, dati: dict | None) -> str | None:
    dati = dati or {}
    for campo in _CAMPI_CODICE:
        valore = dati.get(campo)
        if isinstance(valore, str) and len(valore.strip()) >= 6:
            return valore.strip().upper()
    for testo in (url, titolo):
        trovato = _CODICE_LOMBARDIA.search(testo or "")
        if trovato:
            return trovato.group(1)
    return None


# --- indirizzi ------------------------------------------------------------------------------------

# Parametri che non cambiano la pagina (tracciamento, cache): si tolgono. Gli altri restano, perche' in
# molti siti identificano il bando (?idb=28598, ?id=123).
_PARAMETRI_INUTILI = re.compile(r"^(utm_\w+|fbclid|gclid|t|_|ts|lang|locale|sessionid|jsessionid|phpsessid)$", re.I)


def url_chiave(url: str | None) -> str | None:
    """"https://www.Esempio.it/bandi/x/?utm_source=a#top" -> "esempio.it/bandi/x"."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    parti = urlsplit(url.strip())
    sito = parti.netloc.lower().split("@")[-1]
    sito = sito[4:] if sito.startswith("www.") else sito
    sito = re.sub(r":(80|443)$", "", sito)
    percorso = re.sub(r"/+", "/", parti.path or "/")
    percorso = re.sub(r"/(index|default)\.(html?|php|aspx?)$", "/", percorso, flags=re.I).rstrip("/")
    parametri = sorted((k, v) for k, v in parse_qsl(parti.query, keep_blank_values=True) if not _PARAMETRI_INUTILI.match(k))
    chiave = sito + percorso
    if parametri:
        chiave += "?" + urlencode(parametri)
    return chiave


def _e_pagina_di_servizio(chiave: str) -> bool:
    """Indirizzi che non sono la pagina di un bando: API, dati aperti, feed."""
    return bool(re.search(r"(\.json|\.xml|\.csv|/api/|/feed/?$|/rss)", chiave, re.I))


# --- enti, territori, titoli ----------------------------------------------------------------------

_PAROLE_ENTE = {
    "di", "del", "della", "delle", "dei", "degli", "e", "industria", "artigianato", "agricoltura",
    "autonoma", "c", "i", "a", "commercio", "camera", "cciaa", "provincia", "regione", "comune",
}


def ente_normalizzato(ente: str | None) -> str:
    """"Camera di Commercio, Industria, Artigianato e Agricoltura di Modena" e "CCIAA Modena" -> "camera modena"."""
    if not ente:
        return ""
    testo = normalizza(ente).replace("c.c.i.a.a.", "cciaa")
    tipo = ""
    if re.search(r"\b(cciaa|camera)\b", testo):
        tipo = "camera"
    elif re.search(r"\bregione\b", testo):
        tipo = "regione"
    elif re.search(r"\bcomune\b", testo):
        tipo = "comune"
    elif re.search(r"\bprovincia\b", testo):
        tipo = "provincia"
    parole = [p for p in re.findall(r"[a-z0-9]+", testo) if p not in _PAROLE_ENTE]
    return " ".join(([tipo] if tipo else []) + parole)


def enti_diversi(a: str, b: str) -> bool:
    """Due enti dello stesso tipo ma con nome diverso: "camera bari" e "camera foggia"."""
    tipo_a, _, nome_a = a.partition(" ")
    tipo_b, _, nome_b = b.partition(" ")
    return tipo_a == tipo_b and tipo_a in ("camera", "comune", "provincia") and nome_a != nome_b


REGIONI = {
    "piemonte": "PIE", "valle d'aosta": "VDA", "lombardia": "LOM", "trentino": "TAA", "veneto": "VEN",
    "friuli": "FVG", "liguria": "LIG", "emilia": "EMR", "toscana": "TOS", "umbria": "UMB", "marche": "MAR",
    "lazio": "LAZ", "abruzzo": "ABR", "molise": "MOL", "campania": "CAM", "puglia": "PUG", "basilicata": "BAS",
    "calabria": "CAL", "sicilia": "SIC", "sardegna": "SAR",
}


def territorio_annuncio(territorio_fonte: str, dati: dict | None) -> str:
    """Sigla del territorio: quella della fonte; per i cataloghi nazionali, la regione se ce n'e' una sola
    o se il gestore e' una Regione (il catalogo a volte elenca tutte le regioni anche per un bando regionale)."""
    gestore = normalizza(str((dati or {}).get("gestore") or ""))
    if territorio_fonte == "ITA" and gestore.startswith("regione"):
        for chiave, sigla in REGIONI.items():
            if chiave in gestore:
                return sigla
    regioni = (dati or {}).get("regioni")
    if territorio_fonte == "ITA" and isinstance(regioni, list) and len(regioni) == 1:
        nome = normalizza(str(regioni[0]))
        for chiave, sigla in REGIONI.items():
            if nome.startswith(chiave):
                return sigla
    return territorio_fonte


def territori_compatibili(a: str, b: str) -> bool:
    """Due annunci possono parlare dello stesso bando se stanno nello stesso territorio o uno e' nazionale/UE."""
    if a == b or {"ITA", "UE"} & {a, b}:
        return True
    return {a, b} <= {"TAA", "TN", "BZ"}


_VUOTE = {
    "il", "lo", "la", "i", "gli", "le", "un", "una", "di", "del", "dello", "della", "dei", "degli", "delle",
    "a", "al", "allo", "alla", "ai", "agli", "alle", "da", "dal", "dalla", "dai", "in", "nel", "nella", "nei",
    "nelle", "con", "su", "sul", "sulla", "per", "tra", "fra", "e", "ed", "o", "od", "che", "anno", "anni",
    "annualita", "n", "nr", "art", "s", "l", "d", "it", "www",
    # parole che stanno in quasi ogni titolo e non distinguono un bando da un altro
    "bando", "bandi", "avviso", "pubblico", "pubblicata", "pubblicato", "pubblicate", "approvata", "approvato",
    "approvate", "approvazione", "nuovo", "nuova",
}
_ORDINALI = {
    "primo": 1, "prima": 1, "i": 1, "secondo": 2, "seconda": 2, "ii": 2, "terzo": 3, "terza": 3, "iii": 3,
    "quarto": 4, "quarta": 4, "iv": 4, "quinto": 5, "quinta": 5, "v": 5, "sesto": 6, "sesta": 6, "vi": 6,
}
_EDIZIONE = re.compile(
    r"\b(" + "|".join(_ORDINALI) + r"|\d)\s*(?:°|ª|o|a)?\s*(sportello|edizione|finestra|call|bando|avviso|apertura|tranche|semestre)\b"
    r"|\b(sportello|edizione|finestra|call|tranche|semestre)\s+(" + "|".join(_ORDINALI) + r"|\d)\b"
)
_ANNO = re.compile(r"(?<!\d)(20[0-4]\d)(?!\d)")


# Parti di un programma con regole proprie: "Linea A" e "Linea B", "Avviso n. 2" e "Avviso n. 3" sono bandi diversi.
_PARTE = re.compile(r"\b(linea|misura|lotto|asse|intervento|azione|n|nr|numero)\.?\s+([a-z]|\d+(?:\.\d+)*)\b")


@dataclass(frozen=True)
class Titolo:
    parole: frozenset[str]
    anni: frozenset[str]
    edizione: frozenset[str]
    luoghi: frozenset[str] = frozenset()   # parole del nome dell'ente scritte nel titolo ("Arezzo", "Siena")

    def chiave(self, ente: str) -> str:
        return "|".join([ente, ",".join(sorted(self.anni)), ",".join(sorted(self.edizione)), " ".join(sorted(self.parole))])


# Parole che dicono che l'annuncio aggiorna un bando esistente, per ruolo. Si tolgono dal titolo prima del
# confronto: "Proroga del bando Voucher 2026" deve somigliare a "Bando Voucher 2026".
RUOLI = {
    "graduatoria": r"graduatori\w*|esit[oi]|elench\w* (?:delle )?(?:domande|imprese|beneficiari|ammess\w*)|"
                   r"ammess\w* a contributo|beneficiari ammessi|approvazione (?:dell'|degli |della )?(?:elenc\w*|graduatori\w*)|"
                   r"concessione (?:dei )?contributi (?:alle|ai) (?:imprese|beneficiari)|decreto di concessione",
    "proroga": r"prorog\w*|differiment\w*|riapertura (?:dei )?termini|riapertura|nuova scadenza|spostamento (?:dei )?termini",
    "rettifica": r"rettific\w*|errata corrige|modific\w* (?:al|del|dell'|della) (?:bando|avviso)|integrazion\w* (?:al|del|dell'|della) (?:bando|avviso)",
    "faq": r"faq|domande frequenti|chiarimenti",
    "chiusura": r"chiusura (?:dello |anticipata )?(?:sportello|bando|domande|termini)|esaurimento (?:delle )?risorse|"
                r"sospensione (?:dello |del )?(?:sportello|bando|domande)",
}
_RUOLI = {ruolo: re.compile(r"(?<!\w)(?:" + espressione + r")(?!\w)") for ruolo, espressione in RUOLI.items()}


def ruolo_da_titolo(titolo: str) -> str | None:
    testo = normalizza(titolo)
    for ruolo, espressione in _RUOLI.items():
        if espressione.search(testo):
            return ruolo
    return None


def analizza_titolo(titolo: str, ente_norm: str = "") -> Titolo:
    testo = normalizza(titolo).replace("’", "'")
    anni = frozenset(_ANNO.findall(testo))
    edizione = set()
    for m in _EDIZIONE.finditer(testo):
        numero = m.group(1) or m.group(4)
        tipo = m.group(2) or m.group(3)
        edizione.add(f"{tipo}{_ORDINALI.get(numero, numero)}")
    for m in _PARTE.finditer(testo):
        edizione.add(f"{'n' if m.group(1) in ('n', 'nr', 'numero') else m.group(1)}{m.group(2)}")
    for espressione in _RUOLI.values():
        testo = espressione.sub(" ", testo)
    testo = _PARTE.sub(" ", _EDIZIONE.sub(" ", _ANNO.sub(" ", testo)))
    # Le parole del nome dell'ente ("CCIAA Modena - Bando...") non contano per la somiglianza, ma si tengono
    # a parte: due titoli con luoghi diversi ("... 2026 Arezzo" e "... 2026 Siena") sono bandi diversi.
    del_ente = set(ente_norm.split()) - {"camera", "regione", "comune", "provincia"}
    tutte = [p for p in re.findall(r"[a-z0-9]+", testo)
             if p not in _VUOTE and p not in {"cciaa", "camera", "commercio", "regione", "comune"}
             and len(p) > 1 and not (p.isdigit() and len(p) < 2)]
    return Titolo(frozenset(p for p in tutte if p not in del_ente), anni, frozenset(edizione),
                  frozenset(p for p in tutte if p in del_ente))


def luoghi_diversi(a: Titolo, b: Titolo) -> bool:
    return bool(a.luoghi) and bool(b.luoghi) and not (a.luoghi & b.luoghi)


def jaccard(a: Titolo, b: Titolo) -> float:
    if not a.parole or not b.parole:
        return 0.0
    return len(a.parole & b.parole) / len(a.parole | b.parole)


def somiglianza(a: Titolo, b: Titolo) -> float:
    """Quanto si somigliano due titoli (0-1). Titoli troncati ("...") contano per la parte in comune."""
    if not a.parole or not b.parole:
        return 0.0
    comuni = len(a.parole & b.parole)
    jaccard = comuni / len(a.parole | b.parole)
    piccolo = min(len(a.parole), len(b.parole))
    contenimento = comuni / piccolo if piccolo >= 4 else 0.0
    return max(jaccard, 0.9 * contenimento)


def stessa_edizione(a: Titolo, b: Titolo) -> bool:
    return a.anni == b.anni and a.edizione == b.edizione


def edizione_compatibile(a: Titolo, b: Titolo) -> bool:
    """Uno dei due puo' non dire l'anno (titolo troncato); se lo dicono entrambi, gli anni dell'uno devono stare
    tutti nell'altro ("PR FESR 2021-2027 ... 2026" e "... 2026" si', "2024/2025" e "2025/2026" no)."""
    anni = not a.anni or not b.anni or a.anni <= b.anni or b.anni <= a.anni
    edizione = not a.edizione or not b.edizione or a.edizione == b.edizione
    return anni and edizione


# --- la decisione ---------------------------------------------------------------------------------

SOGLIA_DUBBIO = 0.6     # sotto: bandi diversi. Sopra, ma non uguali: da decidere.
SOGLIA_STESSO = 0.9     # stesso ente, stessa edizione e titoli quasi uguali: stesso bando senza chiedere.


@dataclass
class Annuncio:
    id: int
    fonte_id: str
    url: str
    titolo: str
    ente: str                      # chi pubblica (fonte) o, per i cataloghi, il gestore
    territorio: str
    dati: dict | None = None
    bando_id: int | None = None
    collegato_da: str | None = None
    # calcolati
    codice: str | None = None
    urls: set[str] = field(default_factory=set)
    ente_norm: str = ""
    titolo_an: Titolo | None = None
    ruolo: str | None = None

    def prepara(self) -> "Annuncio":
        self.codice = codice_ufficiale(self.url, self.titolo, self.dati)
        self.urls = {u for u in (url_chiave(self.url), url_chiave((self.dati or {}).get("link_ente"))) if u}
        self.ente_norm = ente_normalizzato(self.ente)
        self.titolo_an = analizza_titolo(self.titolo, self.ente_norm)
        self.ruolo = ruolo_da_titolo(self.titolo)
        return self


@dataclass
class Esito:
    """Cosa fare di un annuncio: collegarlo a un bando, crearne uno nuovo, o lasciarlo in dubbio."""

    azione: str                    # collega | nuovo | dubbio | ignora
    bando: int | None = None       # per collega e dubbio (None = dubbio senza candidato)
    ruolo: str | None = None
    motivo: str = ""
    somiglianza: float | None = None


class Indice:
    """Le chiavi dei bandi gia' noti: codice, indirizzi, titoli. Cresce man mano che si creano bandi."""

    def __init__(self, url_ambigui: set[str], anno_corrente: int | None = None):
        self.anno_corrente = anno_corrente or date.today().year
        self.codici: dict[str, int] = {}
        self.urls: dict[str, int] = {}
        self.titoli: dict[int, list[Annuncio]] = defaultdict(list)
        self.url_ambigui = url_ambigui

    def archivio(self, a: Annuncio) -> bool:
        """Un titolo che cita solo anni di almeno due anni fa ("graduatoria 2022") e' un bando d'archivio:
        non vale la pena chiedere a Matteo se e' un doppione."""
        anni = [int(x) for x in a.titolo_an.anni]
        return bool(anni) and max(anni) <= self.anno_corrente - 2

    def urls_validi(self, a: Annuncio) -> set[str]:
        return {u for u in a.urls if u not in self.url_ambigui and not _e_pagina_di_servizio(u)}

    def aggiungi(self, a: Annuncio, bando: int) -> None:
        if a.codice:
            self.codici.setdefault(a.codice, bando)
        for u in self.urls_validi(a):
            self.urls.setdefault(u, bando)
        self.titoli[bando].append(a)

    def decidi(self, a: Annuncio) -> Esito:
        ruolo_agg = a.ruolo or "doppione"
        if a.codice and a.codice in self.codici:
            return Esito("collega", self.codici[a.codice], ruolo_agg, f"stesso codice {a.codice}")
        for u in sorted(self.urls_validi(a)):
            if u in self.urls:
                bando = self.urls[u]
                s = max(somiglianza(a.titolo_an, b.titolo_an) for b in self.titoli[bando])
                if s < 0.2:
                    # Stessa pagina ma titoli che non c'entrano: spesso il link generico di un ente
                    # ("Contributi e finanziamenti"). Meglio chiedere.
                    return Esito("dubbio", bando, ruolo_agg, f"stesso indirizzo ma titoli diversi ({u[:100]})", s)
                return Esito("collega", bando, ruolo_agg, f"stesso indirizzo {u[:120]}")
        # Titolo: il candidato piu' simile, tra i bandi dello stesso territorio e di edizione compatibile.
        migliore: tuple[float, int, Annuncio] | None = None
        for bando, annunci in self.titoli.items():
            for b in annunci:
                if not territori_compatibili(a.territorio, b.territorio):
                    continue
                if a.codice and b.codice and a.codice != b.codice:
                    continue   # due codici ufficiali diversi: bandi diversi
                if not edizione_compatibile(a.titolo_an, b.titolo_an) or luoghi_diversi(a.titolo_an, b.titolo_an):
                    continue
                s = somiglianza(a.titolo_an, b.titolo_an)
                j = jaccard(a.titolo_an, b.titolo_an)
                # Due enti diversi dello stesso tipo (Camera di Bari e Camera di Foggia) fanno spesso bandi con
                # lo stesso nome: sono doppioni possibili solo con titoli uguali (bandi comuni lombardi).
                if enti_diversi(a.ente_norm, b.ente_norm) and j < SOGLIA_STESSO:
                    continue
                # Nella stessa fonte, due pagine diverse con titoli diversi sono quasi sempre due bandi
                # (linee, destinatari o edizioni diverse).
                if a.fonte_id == b.fonte_id and j < 0.8 and not a.ruolo:
                    continue
                if migliore is None or s > migliore[0]:
                    migliore = (s, bando, b)
        if migliore and migliore[0] >= SOGLIA_DUBBIO:
            s, bando, b = migliore
            j = jaccard(a.titolo_an, b.titolo_an)
            stessa = stessa_edizione(a.titolo_an, b.titolo_an)
            sicuro = (j >= SOGLIA_STESSO and a.ente_norm == b.ente_norm and stessa
                      and (a.titolo_an.anni or a.titolo_an.edizione or a.fonte_id == b.fonte_id))
            if sicuro:
                return Esito("collega", bando, ruolo_agg, f"stesso ente, edizione e titolo (somiglianza {s:.2f})", s)
            if self.archivio(a):
                return Esito("nuovo", None, "origine", f"bando vecchio: simile a annuncio {b.id}, ma non si chiede ({s:.2f})")
            return Esito("dubbio", bando, ruolo_agg, f"titolo simile a annuncio {b.id} (somiglianza {s:.2f})", s)
        if a.ruolo and self.archivio(a):
            return Esito("ignora", None, a.ruolo, f"{a.ruolo} di un bando vecchio, non trovato: si lascia senza bando")
        if a.ruolo:
            return Esito("dubbio", None, a.ruolo, f"{a.ruolo}: non trovo il bando a cui si riferisce")
        return Esito("nuovo", None, "origine", "nuovo bando")


def url_ambigui(annunci: list[Annuncio]) -> set[str]:
    """Indirizzi che nella stessa fonte tornano in piu' annunci: pagine elenco, link generici all'ente."""
    conta: Counter = Counter()
    for a in annunci:
        for u in a.urls:
            conta[(a.fonte_id, u)] += 1
    return {u for (_, u), n in conta.items() if n > 1}


def pianifica(annunci: list[Annuncio], bandi_esistenti: dict[int, list[Annuncio]] | None = None,
              in_dubbio: set[int] | None = None, anno_corrente: int | None = None) -> list[tuple[Annuncio, Esito]]:
    """Decide per ogni annuncio non collegato. Non tocca il database.

    `annunci`: tutti gli annunci rilevanti (collegati e no), gia' preparati.
    I nuovi bandi hanno numeri negativi provvisori (-1, -2...), sostituiti dal numero vero al salvataggio.
    """
    in_dubbio = in_dubbio or set()
    indice = Indice(url_ambigui(annunci), anno_corrente)
    for bando, collegati in (bandi_esistenti or {}).items():
        for a in collegati:
            indice.aggiungi(a, bando)
    piano: list[tuple[Annuncio, Esito]] = []
    prossimo = -1
    for a in annunci:
        if a.bando_id is not None or a.id in in_dubbio:
            continue
        esito = indice.decidi(a)
        if esito.azione == "nuovo":
            esito.bando = prossimo
            prossimo -= 1
            indice.aggiungi(a, esito.bando)
        elif esito.azione == "collega":
            indice.aggiungi(a, esito.bando)
        piano.append((a, esito))
    return piano


# --- database ---------------------------------------------------------------------------------------

def carica(conn) -> tuple[list[Annuncio], dict[int, list[Annuncio]], set[int]]:
    """Annunci rilevanti (dal piu' vecchio: il primo arrivato e' l'origine), bandi esistenti, annunci in dubbio."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id, a.fonte_id, a.url, a.titolo, a.dati, a.bando_id, a.collegato_da,
                   f.ente AS ente_fonte, f.territorio
            FROM annunci a JOIN fonti f ON f.id = a.fonte_id
            WHERE a.bando_id IS NOT NULL
               OR EXISTS (SELECT 1 FROM smistamenti s WHERE s.annuncio_id = a.id AND s.esito = 'rilevante')
            ORDER BY coalesce(a.pubblicato_il, a.trovato_il), a.id
            """
        )
        righe = cur.fetchall()
        cur.execute("SELECT DISTINCT annuncio_id FROM bandi_dubbi WHERE decisione IS NULL")
        in_dubbio = {r["annuncio_id"] for r in cur.fetchall()}
    annunci = []
    for r in righe:
        dati = r["dati"] if isinstance(r["dati"], dict) else None
        ente = (dati or {}).get("gestore") or r["ente_fonte"]
        annunci.append(Annuncio(r["id"], r["fonte_id"], r["url"], r["titolo"], ente,
                                territorio_annuncio(r["territorio"], dati), dati, r["bando_id"],
                                r["collegato_da"]).prepara())
    esistenti: dict[int, list[Annuncio]] = defaultdict(list)
    for a in annunci:
        if a.bando_id is not None:
            esistenti[a.bando_id].append(a)
    return annunci, esistenti, in_dubbio


def _scadenza(dati: dict | None) -> str | None:
    for chiave in ("scadenza", "data_chiusura", "dataScadenza", "deadlineDate", "chiusura_adesione", "data_scadenza"):
        valore = (dati or {}).get(chiave)
        if isinstance(valore, str) and re.match(r"^20\d{2}-\d{2}-\d{2}", valore):
            return valore[:10]
    return None


def _url_pagina(url: str) -> str | None:
    """L'indirizzo da mostrare come pagina del bando: non un'API o un file di dati aperti."""
    chiave = url_chiave(url)
    return url if chiave and not _e_pagina_di_servizio(chiave) else None


def crea_bando(cur, a: Annuncio) -> int:
    """Una scheda minima, senza IA: titolo, ente, territorio, indirizzo e chiavi. Il resto arriva con Sonnet."""
    url_valida = next((u for u in sorted(a.urls) if not _e_pagina_di_servizio(u)), None)
    cur.execute(
        """
        INSERT INTO bandi (annuncio_id, titolo, ente, territorio, url, scadenza, codice_ufficiale, url_chiave, chiave_titolo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """,
        (a.id, a.titolo, a.ente, a.territorio, _url_pagina(a.url), _scadenza(a.dati), a.codice, url_valida,
         a.titolo_an.chiave(a.ente_norm)),
    )
    return cur.fetchone()["id"]


def collega(cur, annuncio_id: int, bando_id: int, ruolo: str, motivo: str, da: str = "regole") -> None:
    """Collega un annuncio a un bando; i suoi allegati passano al bando. Un legame di Matteo resta di Matteo."""
    condizione = "" if da == "matteo" else " AND (collegato_da IS DISTINCT FROM 'matteo')"
    cur.execute(
        f"""UPDATE annunci SET bando_id = %s, ruolo = %s, collegato_da = %s, collegato_il = now(), collegamento_motivo = %s
            WHERE id = %s{condizione}""",
        (bando_id, ruolo, da, motivo[:500], annuncio_id),
    )
    cur.execute("UPDATE allegati SET bando_id = %s WHERE annuncio_id = %s", (bando_id, annuncio_id))
    # Un bando nato da un'API (dati aperti) non ha una pagina da mostrare: la prende dal primo annuncio che ce l'ha.
    cur.execute("SELECT url FROM annunci WHERE id = %s", (annuncio_id,))
    riga = cur.fetchone()
    pagina = _url_pagina(riga["url"]) if riga else None
    if pagina:
        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"annuncio {annuncio_id}: pagina del bando",))
        cur.execute("UPDATE bandi SET url = %s WHERE id = %s AND url IS NULL", (pagina, bando_id))


def leggi_annuncio(cur, annuncio_id: int) -> Annuncio | None:
    cur.execute(
        """SELECT a.id, a.fonte_id, a.url, a.titolo, a.dati, a.bando_id, a.collegato_da, f.ente AS ente_fonte, f.territorio
           FROM annunci a JOIN fonti f ON f.id = a.fonte_id WHERE a.id = %s""",
        (annuncio_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    dati = r["dati"] if isinstance(r["dati"], dict) else None
    return Annuncio(r["id"], r["fonte_id"], r["url"], r["titolo"], (dati or {}).get("gestore") or r["ente_fonte"],
                    territorio_annuncio(r["territorio"], dati), dati, r["bando_id"], r["collegato_da"]).prepara()


def _togli_bandi_vuoti(cur, bandi: set[int]) -> None:
    """Un bando rimasto senza annunci e mai schedato dall'IA non serve piu'."""
    for b in bandi:
        cur.execute("DELETE FROM bandi b WHERE id = %s AND dati IS NULL AND NOT EXISTS "
                    "(SELECT 1 FROM annunci a WHERE a.bando_id = b.id)", (b,))


def decisione_matteo(conn, annuncio_id: int, bando_id: int | None) -> int:
    """Matteo decide dalla plancia: l'annuncio va nel bando `bando_id` (unire, "stesso bando"),
    oppure, con None, diventa un bando a se' (separare, "bandi diversi"). I dubbi dell'annuncio si chiudono.
    Ritorna il bando dell'annuncio. Il legame e' di Matteo: la deduplica automatica non lo cambiera' piu'."""
    with conn.cursor() as cur:
        a = leggi_annuncio(cur, annuncio_id)
        if a is None:
            raise LookupError("annuncio non trovato")
        vecchio = a.bando_id
        cur.execute("SELECT set_config('bandi_radar.causa', %s, true)", (f"annuncio {annuncio_id}: decisione di Matteo",))
        if bando_id is None:
            altri = 0
            if vecchio is not None:
                cur.execute("SELECT count(*) AS n FROM annunci WHERE bando_id = %s AND id <> %s", (vecchio, annuncio_id))
                altri = cur.fetchone()["n"]
            nuovo = vecchio if vecchio is not None and altri == 0 else crea_bando(cur, a)
            collega(cur, annuncio_id, nuovo, "origine", "separato a mano dalla plancia", "matteo")
        else:
            cur.execute("SELECT 1 FROM bandi WHERE id = %s", (bando_id,))
            if not cur.fetchone():
                raise LookupError("bando non trovato")
            nuovo = bando_id
            collega(cur, annuncio_id, nuovo, a.ruolo or "doppione", "unito a mano dalla plancia", "matteo")
        cur.execute(
            """UPDATE bandi_dubbi SET decisione = CASE WHEN bando_id = %s THEN 'stesso' ELSE 'diverso' END,
                      deciso_da = 'matteo', deciso_il = now()
               WHERE annuncio_id = %s AND decisione IS NULL""",
            (nuovo, annuncio_id),
        )
        if vecchio is not None and vecchio != nuovo:
            _togli_bandi_vuoti(cur, {vecchio})
    conn.commit()
    return nuovo


def salva_piano(conn, piano: list[tuple[Annuncio, Esito]]) -> Counter:
    conteggi: Counter = Counter()
    veri: dict[int, int] = {}
    with conn.cursor() as cur:
        for a, e in piano:
            if e.azione == "nuovo":
                veri[e.bando] = crea_bando(cur, a)
                collega(cur, a.id, veri[e.bando], "origine", e.motivo)
            elif e.azione == "collega":
                collega(cur, a.id, veri.get(e.bando, e.bando), e.ruolo or "doppione", e.motivo)
            elif e.azione == "dubbio":
                bando = veri.get(e.bando, e.bando) if e.bando is not None else None
                cur.execute(
                    """INSERT INTO bandi_dubbi (annuncio_id, bando_id, somiglianza, motivo)
                       VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    (a.id, bando, e.somiglianza, e.motivo),
                )
            conteggi[e.azione] += 1
    conn.commit()
    return conteggi


def stampa(piano: list[tuple[Annuncio, Esito]], annunci: list[Annuncio], n_esempi: int) -> None:
    origine: dict[int, Annuncio] = {a.bando_id: a for a in annunci if a.bando_id is not None}
    for a, e in piano:
        if e.azione == "nuovo":
            origine[e.bando] = a
    conteggi = Counter(e.azione for _, e in piano)
    ruoli = Counter(e.ruolo for _, e in piano if e.azione == "collega")
    bandi = len({e.bando for _, e in piano if e.azione in ("nuovo", "collega")} | {a.bando_id for a in annunci if a.bando_id})
    print(f"Annunci rilevanti: {len(annunci)}; da decidere adesso: {len(piano)}")
    print(f"  nuovi bandi:            {conteggi['nuovo']}")
    print(f"  collegati a un bando:   {conteggi['collega']}  ({', '.join(f'{r} {n}' for r, n in ruoli.most_common())})")
    print(f"  dubbi (decide Matteo):  {conteggi['dubbio']}")
    print(f"  lasciati senza bando:   {conteggi['ignora']}  (aggiornamenti di bandi vecchi non trovati)")
    print(f"Bandi in tutto dopo questo giro: {bandi}")
    motivi = Counter(e.motivo.split(" ")[0] + " " + e.motivo.split(" ")[1] for _, e in piano if e.azione == "collega")
    print("Collegati per chiave: " + ", ".join(f"{m} {n}" for m, n in motivi.most_common()))
    print(f"\nEsempi di doppioni e aggiornamenti trovati ({min(n_esempi, conteggi['collega'])}):")
    for a, e in [x for x in piano if x[1].azione == "collega"][:n_esempi]:
        o = origine.get(e.bando)
        print(f"  [{a.id}] {a.fonte_id}: {a.titolo[:80]}")
        print(f"      = [{o.id if o else '?'}] {o.fonte_id if o else ''}: {o.titolo[:80] if o else ''}")
        print(f"      ({e.ruolo}; {e.motivo})")
    print(f"\nEsempi di dubbi ({min(n_esempi, conteggi['dubbio'])}):")
    for a, e in [x for x in piano if x[1].azione == "dubbio"][:n_esempi]:
        o = origine.get(e.bando) if e.bando is not None else None
        print(f"  [{a.id}] {a.fonte_id}: {a.titolo[:80]}")
        print(f"      ? [{o.id if o else '-'}] {o.fonte_id if o else ''}: {o.titolo[:80] if o else ''}")
        print(f"      ({e.motivo})")


def esegui(prova: bool = False, n_esempi: int = 20) -> int:
    from app.db.connessione import connetti
    from app.db.migrazioni import applica_migrazioni

    with connetti() as conn:
        applica_migrazioni(conn)
        annunci, esistenti, in_dubbio = carica(conn)
        piano = pianifica(annunci, esistenti, in_dubbio)
        if prova:
            print("PROVA: nessuna modifica al database.")
        else:
            salva_piano(conn, piano)
    stampa(piano, annunci, n_esempi)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deduplica senza IA: collega gli annunci rilevanti ai bandi.")
    parser.add_argument("--prova", action="store_true", help="non scrive nel database: stampa numeri ed esempi")
    parser.add_argument("--esempi", type=int, default=20, metavar="N", help="quanti esempi stampare (default 20)")
    args = parser.parse_args(argv)
    return esegui(args.prova, args.esempi)


if __name__ == "__main__":
    sys.exit(main())
