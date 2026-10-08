"""Pagina "I miei bandi" (07/10/2026, richiesta di Matteo): i bandi di un profilo divisi in tre gruppi, con le parole
che servono all'impresa e non al motore delle regole.

- adatti: compatibili, tutti i requisiti verificati sui dati del profilo;
- da valutare: da verificare, con il motivo in parole semplici ("serve verificare il codice ATECO");
- altre regioni: da verificare ma pubblicati da enti di un'altra regione (servirebbe una sede o il progetto li').

In ogni gruppo prima il fondo perduto (Matteo, 05/10), poi la scadenza piu' vicina. A parte, le misure nazionali utili
al profilo, con l'esempio pratico del tipo di impresa piu' simile (profili_esempio di app/misure/misure.yaml).
Nessuna IA: solo le regole di app/abbinamento e testi fissi.
"""

from __future__ import annotations

from datetime import date, datetime

from app.abbinamento import catalogo, regole

GIORNI_IN_SCADENZA = 15
GIORNI_NUOVO = 7

_NOMI_TIPI = {"fondo_perduto": "Fondo perduto", "credito_imposta": "Credito d'imposta",
              "finanziamento_agevolato": "Finanziamento agevolato", "garanzia": "Garanzia", "voucher": "Voucher",
              "servizi": "Servizi", "premio": "Premio"}


def _euro(n) -> str:
    return f"{float(n):,.0f} €".replace(",", ".")


def _percento(n) -> str:
    return f"{float(n):g}%".replace(".", ",")


def agevolazione(b: dict) -> str:
    """Tipo e intensita' in una riga: "Fondo perduto 50%, fino a 20.000 €". Solo i dati che la scheda ha."""
    tipi = [t for t in (b.get("tipi_agevolazione") or [b.get("tipo_agevolazione")]) if t and t != "altro"]
    if catalogo.a_fondo_perduto(b) and not any(t in ("fondo_perduto", "voucher", "premio") for t in tipi):
        tipi = ["fondo_perduto", *tipi]
    # Il fondo perduto prima: e' quello che l'impresa guarda per primo.
    tipi.sort(key=lambda t: t not in ("fondo_perduto", "voucher", "premio"))
    parti = []
    if tipi:
        testa = _NOMI_TIPI.get(tipi[0], tipi[0].replace("_", " ").capitalize())
        percentuale = b.get("percentuale_fondo_perduto") if tipi[0] == "fondo_perduto" else None
        percentuale = percentuale if percentuale is not None else b.get("percentuale")
        if percentuale is not None:
            testa += f" {_percento(percentuale)}"
        altri = [_NOMI_TIPI.get(t, t.replace("_", " ")).lower() for t in tipi[1:3]]
        parti.append(testa + (f" + {' + '.join(altri)}" if altri else ""))
    massimo = (b.get("fondo_perduto_massimo") if tipi[:1] == ["fondo_perduto"] else None) \
        or b.get("contributo_massimo") or b.get("fondo_perduto_massimo") or b.get("finanziamento_massimo")
    if massimo:
        parti.append(f"fino a {_euro(massimo)}")
    testo = ", ".join(parti)
    return testo[:1].upper() + testo[1:] if testo else "Agevolazione da leggere nella scheda"


# Dubbi del motore -> parole per l'impresa. Si guarda l'inizio del motivo (le regole sono in app/abbinamento/regole.py).
_SEMPLICI = (
    (("manca il codice ATECO",), "indica il codice ATECO: serve a capire se il tuo settore è ammesso"),
    (("settori ammessi", "ATECO ammesso ma", "ATECO non trovato", "il bando ammette solo alcune sottocategorie"),
     "serve verificare il codice ATECO"),
    (("settore forse escluso",), "serve verificare che il tuo settore non sia escluso"),
    (("territorio non noto, ma il bando è di",), None),   # resta com'e': dice gia' dove
    (("territorio non noto", "territorio scritto solo a parole"), "serve verificare dove vale il bando"),
    (("manca la sede",), "indica la sede dell'impresa"),
    (("beneficiari", "ammessi anche altri soggetti"), "serve verificare che la tua impresa sia tra i beneficiari"),
    (("manca il tipo di soggetto",), "indica se sei un'impresa, un professionista o un ente"),
    (("forme giuridiche", "forme ammesse"), "serve verificare la forma giuridica ammessa"),
    (("manca la forma giuridica",), "indica la forma giuridica"),
    (("dimensioni ammesse",), "serve verificare la dimensione d'impresa ammessa"),
    (("manca la dimensione",), "indica la dimensione dell'impresa (dipendenti e fatturato)"),
    (("ammesse ",), "serve verificare la dimensione (conta il totale di bilancio)"),
    (("età dell'impresa", "limite di età"), "serve verificare l'età dell'impresa richiesta"),
    (("manca la data di costituzione",), "indica la data di costituzione"),
    (("requisiti speciali", "c'è un requisito speciale"), "serve verificare un requisito particolare del bando"),
    (("soglie di numero di dipendenti",), "serve verificare il numero di dipendenti richiesto"),
    (("soglie di fatturato",), "serve verificare il fatturato richiesto"),
    (("stato del bando non noto",), "serve verificare se il bando è aperto: mancano le date"),
    (("scheda fatta solo su una sintesi", "scheda senza documenti"), "serve leggere il bando ufficiale"),
)


def semplice(motivo: str) -> str:
    for inizi, testo in _SEMPLICI:
        if motivo.startswith(inizi):
            return testo or motivo
    if motivo.startswith("serve impresa ") and motivo.endswith(": dato mancante nel profilo"):
        return f"riservato a impresa {motivo[len('serve impresa '):-len(': dato mancante nel profilo')]}: indica se lo sei"
    return motivo


def motivi_semplici(esito: regole.Esito) -> list[str]:
    visti: list[str] = []
    for m in esito.da_verificare:
        s = semplice(m)
        if s not in visti:
            visti.append(s)
    return visti


def motivo(esito: regole.Esito) -> str:
    """Una riga che dice perche' il bando e' nell'elenco."""
    if esito.livello == regole.COMPATIBILE:
        favore = [p for p in esito.punti_a_favore if not p.startswith("premialità")]
        return "Requisiti rispettati: " + "; ".join(favore[:3]) if favore else "Nessun requisito che escluda la tua impresa"
    semplici = motivi_semplici(esito)
    return semplici[0][:1].upper() + semplici[0][1:] if semplici else "Da verificare nel bando ufficiale"


def _giorno(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return v


def gruppo(esito: regole.Esito) -> str:
    if esito.livello == regole.COMPATIBILE:
        return "adatti"
    return "altre_regioni" if esito.fuori_zona else "da_valutare"


def ordina(risultati: list[tuple[dict, regole.Esito]]) -> list[tuple[dict, regole.Esito]]:
    """Adatti, da valutare, altre regioni; in ogni gruppo prima il fondo perduto, in fondo le agevolazioni senza soldi
    (servizi, riconoscimenti: catalogo.secondo_piano), poi la scadenza (senza in fondo)."""
    posto = {"adatti": 0, "da_valutare": 1, "altre_regioni": 2}
    return sorted(risultati, key=lambda x: (posto[gruppo(x[1])], catalogo.secondo_piano(x[0]),
                                            not catalogo.a_fondo_perduto(x[0]),
                                            x[0].get("scadenza") is None, x[0].get("scadenza") or date.max))


def arricchisci(r: dict, b: dict, esito: regole.Esito, oggi: date) -> dict:
    """Aggiunge alla riga dell'elenco quello che serve alla card."""
    scadenza = _giorno(b.get("scadenza"))
    giorni = (scadenza - oggi).days if scadenza else None
    schedato = _giorno(b.get("scheda_il"))
    return {**r, "gruppo": gruppo(esito), "agevolazione": agevolazione(b), "fondo_perduto": catalogo.a_fondo_perduto(b),
            "secondo_piano": catalogo.secondo_piano(b), "motivo": motivo(esito), "da_verificare_semplici": motivi_semplici(esito),
            "giorni_alla_scadenza": giorni, "in_scadenza": giorni is not None and 0 <= giorni <= GIORNI_IN_SCADENZA,
            "nuovo": bool(schedato and (oggi - schedato).days < GIORNI_NUOVO)}


def conteggi(righe: list[dict]) -> dict:
    return {"adatti": sum(r["gruppo"] == "adatti" for r in righe),
            "da_valutare": sum(r["gruppo"] == "da_valutare" for r in righe),
            "altre_regioni": sum(r["gruppo"] == "altre_regioni" for r in righe),
            "in_scadenza": sum(r["in_scadenza"] for r in righe), "nuovi": sum(r["nuovo"] for r in righe),
            # come prima, per chi li legge ancora (email, test)
            "compatibile": sum(r["esito"]["livello"] == regole.COMPATIBILE for r in righe),
            "da_verificare": sum(r["esito"]["livello"] == regole.DA_VERIFICARE for r in righe)}

