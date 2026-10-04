-- Area impresa (05/10/2026, tappa 3 del prodotto indipendente).
-- I dati che identificano il cliente (nome dell'impresa, utente, email) stanno qui; il profilo usato per
-- l'abbinamento resta nella tabella profili, anonimo, con un codice casuale (origine 'impresa'). All'IA non arriva
-- mai nulla di queste tabelle.

-- Chi si registra da solo deve confermare l'indirizzo; chi e' invitato lo conferma aprendo il link dell'invito.
ALTER TABLE utenti ADD COLUMN IF NOT EXISTS email_confermata_il timestamptz;
UPDATE utenti SET email_confermata_il = coalesce(ultimo_accesso, creato_il)
 WHERE email_confermata_il IS NULL AND password_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS imprese (
    id                   bigserial PRIMARY KEY,
    utente_id            bigint NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
    nome                 text NOT NULL,                     -- come l'utente riconosce l'impresa (ragione sociale)
    profilo_codice       text NOT NULL UNIQUE REFERENCES profili(codice) ON UPDATE CASCADE,
    dati                 jsonb NOT NULL DEFAULT '{}',       -- scelte del modulo che non vanno nel profilo (fasce)
    email_settimanale    boolean NOT NULL DEFAULT true,
    codice_disiscrizione text NOT NULL UNIQUE,              -- per il link "non voglio piu' l'email" (senza accesso)
    creata_il            timestamptz NOT NULL DEFAULT now(),
    aggiornata_il        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS imprese_utente ON imprese (utente_id);

-- "Richiedi supporto per la domanda": il servizio di Matteo e dei collaboratori, a success fee.
CREATE TABLE IF NOT EXISTS richieste_supporto (
    id            bigserial PRIMARY KEY,
    impresa_id    bigint NOT NULL REFERENCES imprese(id) ON DELETE CASCADE,
    bando_id      bigint NOT NULL REFERENCES bandi(id) ON DELETE CASCADE,
    utente_id     bigint REFERENCES utenti(id) ON DELETE SET NULL,
    messaggio     text,
    origine       text NOT NULL DEFAULT 'piattaforma' CHECK (origine IN ('piattaforma', 'email')),
    stato         text NOT NULL DEFAULT 'nuova' CHECK (stato IN ('nuova', 'in_corso', 'accettata', 'chiusa')),
    nota          text,                                      -- appunti di Matteo
    creata_il     timestamptz NOT NULL DEFAULT now(),
    aggiornata_il timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS richieste_supporto_stato ON richieste_supporto (stato, creata_il);

-- Email settimanale per impresa: preparata il lunedi', parte dopo l'approvazione di Matteo (fase di prova, 23/09).
CREATE TABLE IF NOT EXISTS email_imprese (
    id          bigserial PRIMARY KEY,
    impresa_id  bigint NOT NULL REFERENCES imprese(id) ON DELETE CASCADE,
    settimana   text NOT NULL,                               -- es. 2026-W41
    bandi       jsonb NOT NULL,                              -- [{bando_id, motivo: nuovo | in_scadenza}]
    oggetto     text NOT NULL,
    testo       text NOT NULL,
    html        text,
    stato       text NOT NULL DEFAULT 'da_approvare'
                CHECK (stato IN ('da_approvare', 'inviata', 'scartata', 'errore')),
    creata_il   timestamptz NOT NULL DEFAULT now(),
    decisa_il   timestamptz,
    decisa_da   text,
    errore      text,
    UNIQUE (impresa_id, settimana)
);

-- Bandi gia' mandati a un'impresa: mai due volte lo stesso.
CREATE TABLE IF NOT EXISTS bandi_segnalati (
    impresa_id    bigint NOT NULL REFERENCES imprese(id) ON DELETE CASCADE,
    bando_id      bigint NOT NULL REFERENCES bandi(id) ON DELETE CASCADE,
    email_id      bigint REFERENCES email_imprese(id) ON DELETE SET NULL,
    segnalato_il  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (impresa_id, bando_id)
);
