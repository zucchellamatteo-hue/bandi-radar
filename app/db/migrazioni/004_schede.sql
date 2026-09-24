-- Fase 3, schede: smistamento degli annunci, allegati scaricati, schede dei bandi.

-- Una scheda = un bando vero, ricavato da un annuncio rilevante (dalla pagina e dagli allegati).
-- I campi sono quelli di docs/SCHEDA_BANDO.md; li compila l'IA (Sonnet), Matteo li controlla e da' un voto.
CREATE TABLE IF NOT EXISTS bandi (
    id                  bigserial PRIMARY KEY,
    annuncio_id         bigint UNIQUE REFERENCES annunci(id) ON DELETE SET NULL,  -- l'annuncio di origine
    titolo              text NOT NULL,
    ente                text,
    territorio          text,
    url                 text,                          -- pagina ufficiale del bando, sempre da mostrare
    stato               text CHECK (stato IN ('aperto', 'chiuso', 'prorogato', 'in_arrivo')),
    data_apertura       date,
    scadenza            date,
    sintesi             text,                          -- 3-5 righe in italiano semplice
    a_chi_si_rivolge    text,
    cosa_finanzia       text,
    tipo_agevolazione   text,                          -- fondo_perduto | credito_imposta | finanziamento_agevolato | garanzia | voucher | misto | altro
    contributo_massimo  numeric,                       -- euro, per singola impresa
    percentuale         numeric,                       -- percentuale massima delle spese coperta (0-100)
    spese_ammesse       text,
    codici_ateco        text[],                        -- codici o prefissi ATECO ammessi (es. '62', '25.62'); vuoto = nessun limite dichiarato
    dimensioni_ammesse  text[],                        -- micro | piccola | media | grande
    requisiti           text,
    tema                text,                          -- digitale | green | internazionalizzazione | investimenti | formazione | ricerca | ...
    qualita             smallint CHECK (qualita BETWEEN 1 AND 5),  -- voto di Matteo sulla scheda
    creato_il           timestamptz NOT NULL DEFAULT now(),
    aggiornato_il       timestamptz NOT NULL DEFAULT now(),
    dati                jsonb                          -- risposta grezza dell'IA, con le fonti interne di ogni campo
);
CREATE INDEX IF NOT EXISTS bandi_scadenza ON bandi (scadenza);

-- Documenti ufficiali (bando, modulistica, decreti, FAQ) scaricati dalla pagina dell'annuncio.
-- Si scaricano prima che esista la scheda: per questo si legano all'annuncio, e al bando quando nasce.
-- Una riga anche per i file non scaricati (troppo grandi, vietati da robots.txt...): 'errore' dice perche',
-- cosi' non si riprova a ogni giro e la plancia lo mostra.
CREATE TABLE IF NOT EXISTS allegati (
    id              bigserial PRIMARY KEY,
    annuncio_id     bigint NOT NULL REFERENCES annunci(id) ON DELETE CASCADE,
    bando_id        bigint REFERENCES bandi(id) ON DELETE SET NULL,
    url             text NOT NULL,
    nome            text NOT NULL,                     -- nome leggibile (testo del link o nome del file)
    tipo            text NOT NULL,                     -- pdf | doc | docx | xls | xlsx | odt | zip | p7m | faq
    dimensione      bigint,                            -- byte
    impronta        text,                              -- sha256 del file: cambia se l'ente sostituisce il documento
    percorso_locale text,                              -- relativo alla cartella degli allegati (ALLEGATI_CARTELLA)
    scaricato_il    timestamptz NOT NULL DEFAULT now(),
    testo_estratto  text,                              -- testo del PDF o della pagina FAQ, troncato
    errore          text,                              -- perche' il file non e' stato scaricato (null se tutto bene)
    UNIQUE (annuncio_id, url)
);
CREATE INDEX IF NOT EXISTS allegati_bando ON allegati (bando_id);

-- Quando e' stata cercata l'ultima volta la pagina dell'annuncio per gli allegati: senza questa data
-- le pagine senza documenti verrebbero riaperte a ogni giro.
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS allegati_cercati_il timestamptz;

-- Smistamento: una riga per annuncio con la decisione corrente (rilevante per imprese o no).
-- La decidono le regole (app/schede/regole_smistamento.yaml), poi l'IA per i "da_rivedere", e Matteo
-- puo' correggerla dalla plancia.
-- Storico delle correzioni, nella forma piu' semplice: quando Matteo corregge, la decisione automatica
-- che sta sostituendo (regole o IA) resta nelle colonne proposta_*. Basta per contare dove sbagliano
-- le regole e tararle; se Matteo cambia idea piu' volte resta la prima proposta automatica, non ogni passaggio.
CREATE TABLE IF NOT EXISTS smistamenti (
    annuncio_id     bigint PRIMARY KEY REFERENCES annunci(id) ON DELETE CASCADE,
    esito           text NOT NULL CHECK (esito IN ('rilevante', 'non_rilevante', 'da_rivedere')),
    motivo          text,                              -- per le regole: quale regola e quale parola sono scattate
    deciso_da       text NOT NULL CHECK (deciso_da IN ('regole', 'ia', 'matteo')),
    costo           numeric,                           -- euro spesi per questa decisione (null per regole e Matteo)
    deciso_il       timestamptz NOT NULL DEFAULT now(),
    proposta_esito  text CHECK (proposta_esito IN ('rilevante', 'non_rilevante', 'da_rivedere')),
    proposta_motivo text,
    proposta_da     text CHECK (proposta_da IN ('regole', 'ia'))
);
CREATE INDEX IF NOT EXISTS smistamenti_esito ON smistamenti (esito);
