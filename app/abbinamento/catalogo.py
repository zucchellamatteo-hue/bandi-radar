"""Catalogo dei bandi con scheda: filtri della plancia e abbinamento dei profili usano le stesse regole
(app/abbinamento/regole.py). Le schede sono poche migliaia: si leggono tutte e si filtrano in Python, cosi' la
regola dei tre stati (vincolo / nessun vincolo / non noto) e' scritta in un posto solo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.abbinamento import regole
from app.abbinamento.territorio import regione_della_provincia
from app.schede.campi import REGIONI

# Campi della scheda che servono all'abbinamento e all'elenco (niente testi lunghi, salvo la sintesi).
COLONNE = """b.id, b.titolo, b.ente, b.gestore, b.territorio, b.url, b.stato, b.data_apertura, b.scadenza, b.ora_scadenza,
    b.sintesi, b.tipo_agevolazione, b.tipi_agevolazione, b.temi, b.categorie_spesa, b.contributo_massimo, b.percentuale,
    b.fondo_perduto_massimo, b.percentuale_fondo_perduto, b.finanziamento_massimo, b.contributo_minimo, b.dotazione,
    b.spesa_minima, b.spesa_massima, b.modalita_selezione, b.completezza, b.vincoli, b.linee, b.esclusioni,
    b.territorio_regioni, b.territorio_province, b.territorio_comuni, b.sede_richiesta, b.soggetti_ammessi,
    b.forme_giuridiche_ammesse, b.forme_giuridiche_escluse, b.dimensioni_ammesse, b.eta_impresa_min_mesi,
    b.eta_impresa_max_mesi, b.requisiti_speciali_obbligatori, b.requisiti_speciali_premiali, b.dipendenti_min,
    b.dipendenti_max, b.fatturato_min, b.fatturato_max, b.codici_ateco, b.codici_ateco_esclusi, b.ateco_versione,
    b.regime_aiuto, b.qualita"""

# Stato "aperti": aperti e in arrivo (quello che serve a un cliente). Senza date lo stato non e' noto.
STATI_FILTRO = {"aperti": ("aperto", "in_arrivo"), "aperto": ("aperto",), "in_arrivo": ("in_arrivo",),
                "chiuso": ("chiuso",), "non_noto": (None,), "tutti": None}


def carica_bandi(conn) -> list[dict]:
    """Tutti i bandi con una scheda, con il livello delle fonti (UE, nazionale, regione...) e le loro regioni."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT {COLONNE},
                   coalesce((SELECT array_agg(DISTINCT f.tipo) FROM annunci a JOIN fonti f ON f.id = a.fonte_id
                             WHERE a.bando_id = b.id), '{{}}') AS livelli,
                   coalesce((SELECT array_agg(DISTINCT f.territorio) FROM annunci a JOIN fonti f ON f.id = a.fonte_id
                             WHERE a.bando_id = b.id), '{{}}') AS territori_fonti
            FROM bandi b WHERE b.completezza IS NOT NULL
              -- non per imprese (preliminare o ricontrollo del 03/10): fuori dal catalogo, la scheda resta nello storico
              AND coalesce(b.preliminare->>'per_imprese', '') <> 'no'""")
        bandi = [dict(r) for r in cur.fetchall()]
    for b in bandi:
        b["regioni_fonti"] = [t for t in b["territori_fonti"] if t in REGIONI]
    return bandi


@dataclass
class Filtri:
    q: str | None = None
    stato: str = "aperti"
    scadenza_entro: int | None = None
    livello: str | None = None             # tipo di fonte: ue, nazionale, regione, camera, capoluogo...
    regione: str | None = None
    provincia: str | None = None
    comune: str | None = None
    soggetto: str | None = None
    forma_giuridica: str | None = None
    dimensione: str | None = None
    ateco: str | None = None
    requisito: str | None = None            # bandi riservati o con punti per questo requisito speciale
    tipo_agevolazione: str | None = None
    tema: str | None = None
    categoria_spesa: str | None = None
    modalita: str | None = None
    regime: str | None = None
    # Bandi "in disparte" (01/10, Matteo): scheda non fatta sul bando ufficiale, quindi non proponibile ai clienti.
    # "no" = solo i proponibili (di base), "anche" = tutti, "solo" = solo quelli in disparte.
    in_disparte: str = "no"

    def profilo(self) -> dict:
        """I filtri su chi puo' partecipare diventano un profilo parziale."""
        # Piu' regioni (scelta multipla, "LOM,PIE"): una sede per regione, quindi passa il bando di almeno una.
        # Provincia e comune restano uno solo e completano la loro regione.
        regioni = [r for r in (self.regione or "").split(",") if r]
        principale = {k: v for k, v in (("provincia", self.provincia), ("comune", self.comune)) if v}
        if principale:
            principale["regione"] = regione_della_provincia(self.provincia) if self.provincia else (regioni[:1] or [None])[0]
            principale = {k: v for k, v in principale.items() if v}
        sedi = [principale] if principale else []
        sedi += [{"regione": r} for r in regioni if r != (principale or {}).get("regione")]
        return {"sedi": sedi,"soggetto": self.soggetto, "forma_giuridica": self.forma_giuridica,
                "dimensione": self.dimensione, "ateco": [self.ateco] if self.ateco else []}


def _passa_campi(b: dict, f: Filtri, oggi: date) -> bool:
    stati = STATI_FILTRO.get(f.stato, STATI_FILTRO["aperti"])
    if stati is not None and b["stato"] not in stati:
        return False
    if f.scadenza_entro and not (b["scadenza"] and oggi <= b["scadenza"] <= oggi + timedelta(days=f.scadenza_entro)):
        return False
    if f.q:
        testo = " ".join(str(b.get(k) or "") for k in ("titolo", "ente", "gestore", "sintesi")).lower()
        if not all(parola in testo for parola in f.q.lower().split()):
            return False
    if f.livello and f.livello not in b["livelli"]:
        return False
    if f.requisito and f.requisito not in (b["requisiti_speciali_obbligatori"] or []) + (b["requisiti_speciali_premiali"] or []):
        return False
    for filtro, campo in ((f.tipo_agevolazione, "tipi_agevolazione"), (f.tema, "temi"),
                          (f.categoria_spesa, "categorie_spesa"), (f.regime, "regime_aiuto")):
        if filtro and filtro not in (b[campo] or []):
            return False
    if f.modalita and b["modalita_selezione"] != f.modalita:
        return False
    if f.in_disparte != "anche" and proponibile(b) != (f.in_disparte == "no"):
        return False
    return True


def filtra(bandi: list[dict], f: Filtri, oggi: date | None = None) -> list[tuple[dict, regole.Esito]]:
    """I bandi che passano i filtri, con l'esito delle regole: compatibili prima, poi da verificare; mai gli esclusi.
    Ordine: livello, poi scadenza."""
    oggi = oggi or date.today()
    profilo = f.profilo()
    risultato = []
    for b in bandi:
        if not _passa_campi(b, f, oggi):
            continue
        esito = regole.valuta(b, profilo, oggi, parziale=True)
        if esito.livello != regole.ESCLUSO:
            risultato.append((b, esito))
    risultato.sort(key=lambda x: regole.chiave_ordine(*x))
    return risultato


# Tipi che danno soldi che non si restituiscono: vengono prima nelle proposte alle imprese (Matteo, 05/10/2026).
_A_FONDO_PERDUTO = {"fondo_perduto", "voucher", "premio"}


def a_fondo_perduto(b: dict) -> bool:
    return bool(b.get("fondo_perduto_massimo")) or bool(_A_FONDO_PERDUTO & set(b.get("tipi_agevolazione") or [])) \
        or b.get("tipo_agevolazione") in _A_FONDO_PERDUTO


def prima_il_fondo_perduto(risultati: list[tuple[dict, regole.Esito]]) -> list[tuple[dict, regole.Esito]]:
    """Riordina un elenco gia' ordinato dall'abbinamento: dentro ogni livello (compatibili, da verificare) prima i bandi
    a fondo perduto, poi gli altri (prestiti, garanzie, crediti d'imposta), lasciando invariato il resto dell'ordine.
    E' solo l'ordine di presentazione: chi passa e chi no lo decidono le regole, uguali per tutti."""
    livelli = {regole.COMPATIBILE: 0, regole.DA_VERIFICARE: 1}
    return sorted(risultati, key=lambda x: (livelli.get(x[1].livello, 2), not a_fondo_perduto(x[0])))


def proponibile(b: dict) -> bool:
    """Si propone ai clienti solo un bando con la scheda fatta sul bando ufficiale (Matteo, 01/10/2026): una sintesi,
    una notizia o la scheda del catalogo non bastano. Gli altri restano "in disparte"."""
    return b.get("completezza") == "bando_ufficiale"


def abbina(bandi: list[dict], profilo: dict, oggi: date | None = None, anche_esclusi: bool = False,
           in_disparte: bool = False) -> list[tuple[dict, regole.Esito]]:
    """I bandi aperti o in arrivo (o senza stato noto) per un profilo vero, compatibili prima. Con `in_disparte`, i
    bandi non proponibili (scheda senza bando ufficiale) invece di quelli proponibili."""
    oggi = oggi or date.today()
    risultato = []
    for b in bandi:
        if b["stato"] == "chiuso" or proponibile(b) == in_disparte:
            continue
        esito = regole.valuta(b, profilo, oggi)
        if anche_esclusi or esito.livello != regole.ESCLUSO:
            risultato.append((b, esito))
    risultato.sort(key=lambda x: regole.chiave_ordine(*x))
    return risultato


# Campi che l'elenco mostra (i vincoli restano nella pagina del bando).
CAMPI_RIGA = ("id", "titolo", "ente", "territorio", "url", "stato", "data_apertura", "scadenza", "ora_scadenza",
              "tipo_agevolazione", "tipi_agevolazione", "contributo_massimo", "percentuale", "fondo_perduto_massimo",
              "finanziamento_massimo", "dotazione", "modalita_selezione", "completezza", "livelli", "temi", "qualita")


def riga(b: dict, esito: regole.Esito) -> dict:
    return {**{k: b.get(k) for k in CAMPI_RIGA}, "sintesi": (b.get("sintesi") or "")[:260], "esito": esito.come_dict()}
