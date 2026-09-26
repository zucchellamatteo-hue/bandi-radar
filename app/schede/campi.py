"""I campi della scheda che servono all'abbinamento, con i loro valori ammessi. Un solo posto per tutti:
li usano il prompt per Sonnet (app/schede/prompt_scheda.md), la verifica automatica delle risposte,
la plancia e, dalla Fase 4, il motore di abbinamento. Descrizione e regole di confronto: docs/SCHEDA_BANDO.md.

Se aggiungi o cambi un valore qui, aggiorna anche docs/SCHEDA_BANDO.md e il prompt.
"""

from __future__ import annotations

from datetime import date

# Tre stati per ogni vincolo: l'abbinamento non tratta mai "non_noto" come "va bene".
STATI_VINCOLO = ("vincolo", "nessun_vincolo", "non_noto")

# I vincoli che la scheda dichiara uno per uno (chiavi del campo `vincoli`).
VINCOLI = (
    "territorio", "soggetti", "forme_giuridiche", "dimensioni", "ateco", "eta_impresa",
    "requisiti_speciali", "dipendenti", "fatturato", "spesa", "regime_aiuto",
)

# Quanto la scheda e' affidabile: su cosa e' stata fatta.
COMPLETEZZA = ("bando_ufficiale", "solo_sintesi", "nessun_documento")

# Regioni e Province autonome: le stesse sigle del registro delle fonti (fonti/*.yaml, campo territorio).
REGIONI = ("ABR", "BAS", "BZ", "CAL", "CAM", "EMR", "FVG", "LAZ", "LIG", "LOM", "MAR", "MOL", "PIE", "PUG",
           "SAR", "SIC", "TN", "TOS", "UMB", "VDA", "VEN")

SEDE_RICHIESTA = ("legale", "operativa", "legale_o_operativa", "da_attivare")

SOGGETTI = (
    "impresa",                 # imprese iscritte al Registro delle imprese (anche ditte individuali)
    "libero_professionista",   # professionisti con partita IVA, anche in forma associata
    "aspirante_imprenditore",  # persone che devono ancora costituire l'impresa
    "ente_terzo_settore",      # associazioni, fondazioni, cooperative sociali, ETS
    "ente_pubblico",
    "persona_fisica",
    "altro",
)

FORME_GIURIDICHE = (
    "ditta_individuale", "snc", "sas", "srl", "srls", "spa", "sapa", "societa_semplice", "cooperativa",
    "consorzio", "rete_imprese", "associazione_professionale", "stp", "altro",
)

DIMENSIONI = ("micro", "piccola", "media", "grande")

REQUISITI_SPECIALI = (
    "femminile", "giovanile", "startup_innovativa", "pmi_innovativa", "artigiana", "agricola", "commerciale",
    "turistica", "impresa_sociale", "rating_legalita", "certificazione_parita_genere", "esportatrice",
    "nuova_impresa", "altro",
)

REGIMI_AIUTO = ("de_minimis", "de_minimis_agricolo", "gber", "aber", "temporary_framework", "notificato",
                "non_aiuto", "altro")

VERSIONI_ATECO = ("2007", "2025", "incoerente")

TIPI_AGEVOLAZIONE = ("fondo_perduto", "credito_imposta", "finanziamento_agevolato", "garanzia", "voucher",
                     "servizi", "premio", "altro")

TEMI = ("digitale", "green", "internazionalizzazione", "investimenti", "formazione", "ricerca", "assunzioni",
        "avvio_impresa", "turismo", "commercio", "agricoltura", "cultura", "credito", "sicurezza", "altro")

CATEGORIE_SPESA = (
    "macchinari_attrezzature", "opere_edili_impianti", "software_digitale", "consulenze", "formazione",
    "personale", "fiere_eventi", "marketing_promozione", "brevetti_certificazioni", "veicoli",
    "energia_efficienza", "scorte_circolante", "immobili", "affitto_gestione", "ricerca_sviluppo", "altro",
)

MODALITA_SELEZIONE = ("sportello", "sportello_valutativo", "graduatoria", "click_day", "automatica", "negoziale",
                      "altro")

STATI_BANDO = ("in_arrivo", "aperto", "chiuso")

# --- Dettagli chiesti da Matteo il 25/09 sera: quelli che un commercialista guarda per dire se e quanto conviene.
# Sei blocchi (colonne JSON della tabella bandi), per non moltiplicare i campi: servono alla lettura e ai calcoli,
# l'abbinamento li usa solo per ordinare e per la lista "da controllare con il cliente".

# Intensita' dell'aiuto: percentuale base, eventuale percentuale per dimensione, maggiorazioni.
MOTIVI_MAGGIORAZIONE = (
    "micro", "piccola", "zona_assistita", "area_interna_montana", "femminile", "giovanile", "nuova_impresa",
    "startup_innovativa", "rating_legalita", "certificazione_parita_genere", "aggregazione", "assunzioni", "altro",
)

# Parte a prestito: tipo di tasso.
TIPI_TASSO = ("zero", "fisso", "variabile", "riferimento_ue", "altro")

# Vincoli sulle spese: ogni voce ha uno stato (STATI_VINCOLO) e il dettaglio a parole.
VINCOLI_SPESA = (
    "fornitore",              # niente parti correlate, soci, parenti; fornitori accreditati o iscritti a elenchi
    "bene_nuovo",             # solo beni nuovi di fabbrica
    "bene_usato",             # usato escluso o ammesso a condizioni
    "origine_bene",           # origine UE, "made in", produzione nel territorio
    "leasing_noleggio",       # leasing, noleggio, acquisto a rate
    "pagamento",              # tracciabile, conto dedicato, niente contanti o compensazioni
    "decorrenza",             # da quando le spese valgono (dopo la domanda, dopo la concessione, da una data)
    "iva",                    # IVA ammessa o no
    "tetti_per_voce",         # es. consulenze al massimo il 20% del progetto
    "forfait",                # spese riconosciute a forfait
)

# Esclusioni per tipo di soggetto (i settori stanno in codici_ateco_esclusi, piu' il testo in esclusioni.settori).
ESCLUSIONI_SOGGETTI = (
    "impresa_difficolta", "procedure_concorsuali", "liquidazione", "aiuti_illegali_da_restituire",
    "irregolarita_contributiva", "sanzioni_interdittive", "antimafia", "altri_aiuti_stesse_spese", "altro",
)

# Come arrivano i soldi.
EROGAZIONE = ("anticipo", "stato_avanzamento", "saldo", "unica_soluzione", "compensazione_f24", "altro")

# Cosa serve per presentare la domanda.
REQUISITI_DOMANDA = (
    "spid_cie_cns", "firma_digitale", "pec", "marca_da_bollo", "preventivi", "perizia", "business_plan",
    "relazione_tecnica", "durc", "rating_legalita", "intermediario", "altro",
)

# Struttura dei sei blocchi: campi numerici, campi di testo, campi a valori ammessi (elenco o singolo).
DETTAGLI: dict[str, dict[str, tuple]] = {
    "intensita": {"numerici": ("percentuale_base",), "testi": ("note",)},
    "finanziamento": {
        "numerici": ("quota_fondo_perduto", "percentuale_finanziamento", "tasso_valore", "durata_mesi",
                     "preammortamento_mesi", "garanzia_pubblica_copertura"),
        "testi": ("tasso_note", "garanzie_richieste"),
    },
    "esclusioni": {"numerici": (), "testi": ("settori", "spese")},
    "obblighi": {
        "numerici": ("durata_progetto_mesi", "anticipo_percentuale", "mantenimento_anni"),
        "testi": ("mantenimento_note", "cumulabilita", "rendicontazione"),
    },
    "domanda": {"numerici": (), "testi": ("piattaforma", "criteri_punteggio", "note")},
}
VALORI_AMMESSI_DETTAGLI: dict[str, tuple[str, ...]] = {
    "intensita.maggiorazioni.motivo": MOTIVI_MAGGIORAZIONE,
    "finanziamento.tasso_tipo": TIPI_TASSO,
    "esclusioni.soggetti": ESCLUSIONI_SOGGETTI,
    "obblighi.erogazione": EROGAZIONE,
    "domanda.requisiti": REQUISITI_DOMANDA,
}
PERCENTUALI_DETTAGLI = ("intensita.percentuale_base", "finanziamento.quota_fondo_perduto",
                        "finanziamento.percentuale_finanziamento", "finanziamento.garanzia_pubblica_copertura",
                        "obblighi.anticipo_percentuale")


# Valori ammessi per ogni campo a elenco o a valore singolo della scheda (e delle sue linee).
VALORI_AMMESSI: dict[str, tuple[str, ...]] = {
    "territorio_regioni": REGIONI,
    "sede_richiesta": SEDE_RICHIESTA,
    "soggetti_ammessi": SOGGETTI,
    "forme_giuridiche_ammesse": FORME_GIURIDICHE,
    "forme_giuridiche_escluse": FORME_GIURIDICHE,
    "dimensioni_ammesse": DIMENSIONI,
    "requisiti_speciali_obbligatori": REQUISITI_SPECIALI,
    "requisiti_speciali_premiali": REQUISITI_SPECIALI,
    "regime_aiuto": REGIMI_AIUTO,
    "ateco_versione": VERSIONI_ATECO,
    "tipi_agevolazione": TIPI_AGEVOLAZIONE,
    "temi": TEMI,
    "categorie_spesa": CATEGORIE_SPESA,
    "modalita_selezione": MODALITA_SELEZIONE,
    "completezza": COMPLETEZZA,
}

# Campi numerici della scheda: importi in euro, percentuali 0-100, mesi, persone.
NUMERICI = (
    "contributo_massimo", "percentuale", "fondo_perduto_massimo", "percentuale_fondo_perduto", "finanziamento_massimo",
    "dotazione", "spesa_minima", "spesa_massima", "dipendenti_min", "dipendenti_max", "fatturato_min", "fatturato_max",
    "eta_impresa_min_mesi", "eta_impresa_max_mesi", "contributo_minimo",
)
PERCENTUALI = ("percentuale", "percentuale_fondo_perduto")


def calcola_stato(apertura: date | None, scadenza: date | None, oggi: date, chiuso_il: date | None = None) -> str | None:
    """Lo stato lo calcola il sistema ogni giorno dalle date, non lo scrive l'IA.

    - chiuso: passata la scadenza, o chiuso prima del tempo (fondi esauriti, sospensione: `chiuso_il`);
    - in_arrivo: la data di apertura non e' ancora arrivata;
    - aperto: aperto e non scaduto (anche a sportello senza scadenza);
    - None: non si sa (nessuna data).
    "Prorogato" non e' uno stato ma un evento: si vede nello storico delle versioni.
    """
    if chiuso_il and chiuso_il <= oggi:
        return "chiuso"
    if scadenza and scadenza < oggi:
        return "chiuso"
    if apertura and apertura > oggi:
        return "in_arrivo"
    if apertura or scadenza:
        return "aperto"
    return None
