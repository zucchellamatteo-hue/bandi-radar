-- Parte 3 del 25/09: i campi della scheda che servono all'abbinamento con i profili anonimi dei clienti.
-- Valori ammessi in app/schede/campi.py; descrizione e regole di confronto in docs/SCHEDA_BANDO.md.
-- Migrazione aggiuntiva: i campi esistenti restano (per il catalogo e per le schede gia' fatte), i nuovi si aggiungono.

-- Chi finanzia e chi gestisce: `ente` resta chi mette i soldi (Regione, Camera...), `gestore` chi gestisce il bando
-- (Unioncamere, Invitalia, Finpiemonte...).
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS gestore text;

-- Territorio in codici: sigle delle regioni come nel registro (LOM, FVG...), sigle delle province (MI, BA...),
-- nomi dei comuni (il codice ISTAT lo aggiunge il sistema in Fase 4). Vuoti tutti e tre = tutta Italia,
-- se vincoli->>'territorio' = 'nessun_vincolo'.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS territorio_regioni text[];
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS territorio_province text[];
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS territorio_comuni text[];
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS sede_richiesta text;                -- legale | operativa | legale_o_operativa | da_attivare

-- Chi puo' partecipare.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS soggetti_ammessi text[];            -- impresa, libero_professionista, ...
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS forme_giuridiche_ammesse text[];    -- srl, snc, ditta_individuale, ...
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS forme_giuridiche_escluse text[];
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS eta_impresa_min_mesi integer;       -- es. "attiva da almeno 12 mesi"
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS eta_impresa_max_mesi integer;       -- es. "startup da non piu' di 24 mesi"
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS requisiti_speciali_obbligatori text[];  -- femminile, giovanile, startup_innovativa...
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS requisiti_speciali_premiali text[];     -- danno punti o maggiorazioni, non escludono
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS dipendenti_min numeric;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS dipendenti_max numeric;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS fatturato_min numeric;              -- euro
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS fatturato_max numeric;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS regime_aiuto text[];                -- de_minimis, gber, ...
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS ateco_versione text;                -- 2007 | 2025 | incoerente

-- Cosa e quanto.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS tipi_agevolazione text[];           -- piu' di uno: fondo_perduto + finanziamento...
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS temi text[];
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS categorie_spesa text[];
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS fondo_perduto_massimo numeric;      -- euro: la sola quota a fondo perduto
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS percentuale_fondo_perduto numeric;  -- 0-100: la sola quota a fondo perduto
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS finanziamento_massimo numeric;      -- euro: la parte a prestito, se c'e'
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS spesa_minima numeric;               -- euro: progetto minimo
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS spesa_massima numeric;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS dotazione numeric;                  -- euro: fondi totali del bando

-- Come e quando.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS modalita_selezione text;            -- sportello | graduatoria | click_day | ...
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS ora_apertura time;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS ora_scadenza time;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS chiuso_il date;                     -- chiuso prima del tempo (fondi esauriti, sospeso)
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS stato_calcolato_il date;            -- lo stato lo calcola il sistema ogni giorno

-- Tre stati per ogni vincolo ({"ateco": "vincolo", "dimensioni": "nessun_vincolo", "fatturato": "non_noto", ...}),
-- grado di completezza della scheda, linee del bando (elenco facoltativo, ognuna con i suoi massimali e beneficiari).
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS vincoli jsonb;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS completezza text
    CHECK (completezza IN ('bando_ufficiale', 'solo_sintesi', 'nessun_documento'));
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS linee jsonb;

CREATE INDEX IF NOT EXISTS bandi_regioni ON bandi USING gin (territorio_regioni);
CREATE INDEX IF NOT EXISTS bandi_stato ON bandi (stato);
