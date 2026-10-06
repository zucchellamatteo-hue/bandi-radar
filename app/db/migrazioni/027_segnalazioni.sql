-- Segnalazioni rapide (06/10/2026, richiesta di Matteo): il pulsante "Segnala" sempre visibile nella plancia.
-- Chiunque abbia fatto l'accesso segnala un bando mancante, un errore, un doppione, un problema della plancia o un'idea;
-- Matteo e gli agenti delle sessioni le leggono (pagina Segnalazioni, python -m app.segnalazioni) e le chiudono con
-- una risposta. Diverse dai giudizi sulle schede (tabella feedback): non servono un bando ne' una versione della scheda.
CREATE TABLE IF NOT EXISTS segnalazioni (
    id           bigserial PRIMARY KEY,
    tipo         text NOT NULL CHECK (tipo IN ('manca_bando', 'errore_scheda', 'stato_scadenza', 'doppione', 'documenti',
                                               'plancia', 'idea', 'altro')),
    testo        text,                                   -- testo libero di chi scrive
    dettagli     jsonb NOT NULL DEFAULT '{}',            -- campi del tipo: nome e link del bando, campo sbagliato...
    bando_id     bigint REFERENCES bandi(id) ON DELETE SET NULL,
    pagina       text,                                   -- indirizzo della plancia da cui e' partita
    utente_id    bigint REFERENCES utenti(id) ON DELETE SET NULL,
    ruolo        text,                                   -- ruolo di chi scrive quando scrive
    stato        text NOT NULL DEFAULT 'nuova' CHECK (stato IN ('nuova', 'presa_in_carico', 'risolta', 'respinta')),
    risposta     text,                                   -- spiegazione per chi ha scritto
    creata_il    timestamptz NOT NULL DEFAULT now(),
    gestita_il   timestamptz,
    gestita_da   text                                    -- email dell'admin o "agente"
);
CREATE INDEX IF NOT EXISTS segnalazioni_stato ON segnalazioni (stato, creata_il);
CREATE INDEX IF NOT EXISTS segnalazioni_tipo ON segnalazioni (tipo, stato);
