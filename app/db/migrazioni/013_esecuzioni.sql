-- Supervisione (01/10/2026, richiesta di Matteo): ogni sistema automatico scrive qui quando parte e quando finisce,
-- con l'esito e un riepilogo. La pagina Supervisione della plancia mostra cosa e' in corso, cosa e' andato e quando
-- ripartira'. Elenco dei sistemi e spiegazioni: app/sistemi.py.
CREATE TABLE IF NOT EXISTS esecuzioni (
    id          bigserial PRIMARY KEY,
    sistema     text NOT NULL,
    iniziato_il timestamptz NOT NULL DEFAULT now(),
    finito_il   timestamptz,
    esito       text NOT NULL DEFAULT 'in_corso' CHECK (esito IN ('in_corso', 'ok', 'errore')),
    riepilogo   text,
    errore      text
);
CREATE INDEX IF NOT EXISTS esecuzioni_sistema ON esecuzioni (sistema, iniziato_il DESC);
