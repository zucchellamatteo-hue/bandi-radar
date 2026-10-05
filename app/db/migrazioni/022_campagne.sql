-- Campagne di lancio (05/10/2026): profili ANONIMI delle imprese prospect di Matteo (strumenti/anagrafiche/
-- esporta_profili.py, codice casuale, niente nomi/P.IVA/email) abbinati ai bandi recenti, per preparare lettere o
-- newsletter (a chi ha dato il consenso) che Matteo completa sul suo computer con la corrispondenza codice -> impresa.
CREATE TABLE IF NOT EXISTS campagne (
    id         bigserial PRIMARY KEY,
    nome       text NOT NULL,
    giorni     integer NOT NULL DEFAULT 60,          -- bandi con la scheda fatta negli ultimi N giorni
    stato      text NOT NULL DEFAULT 'in_analisi' CHECK (stato IN ('in_analisi', 'pronta', 'errore')),
    riepilogo  jsonb,
    creata_il  timestamptz NOT NULL DEFAULT now(),
    creata_da  text
);

CREATE TABLE IF NOT EXISTS prospetti (
    id             bigserial PRIMARY KEY,
    campagna_id    bigint NOT NULL REFERENCES campagne(id) ON DELETE CASCADE,
    codice         text NOT NULL,
    profilo        jsonb NOT NULL,
    bandi          jsonb,                             -- [{bando_id, titolo, ente, scadenza, importo, percentuale, livello}]
    n_compatibili  integer NOT NULL DEFAULT 0,
    n_da_verificare integer NOT NULL DEFAULT 0,
    beneficio_max  numeric,
    UNIQUE (campagna_id, codice)
);
CREATE INDEX IF NOT EXISTS prospetti_campagna ON prospetti (campagna_id, n_compatibili DESC);
