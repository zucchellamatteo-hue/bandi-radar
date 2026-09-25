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
    "eta_impresa_min_mesi", "eta_impresa_max_mesi",
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
