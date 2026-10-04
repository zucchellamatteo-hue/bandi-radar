-- Abbonamenti (05/10/2026, tappa 4 del prodotto indipendente): un abbonamento per utente impresa, pagato con Stripe.
-- Stripe tiene carta e addebiti; qui si tiene lo stato che decide l'accesso all'area impresa (solo con
-- ABBONAMENTI_ATTIVI=1: prima tutti entrano come oggi). "gratuito" lo imposta Matteo (imprese amiche, prove).
CREATE TABLE IF NOT EXISTS abbonamenti (
    utente_id           bigint PRIMARY KEY REFERENCES utenti(id) ON DELETE CASCADE,
    stato               text NOT NULL DEFAULT 'prova'
                        CHECK (stato IN ('prova', 'attivo', 'in_ritardo', 'disdetto', 'gratuito')),
    piano               text CHECK (piano IN ('mensile', 'annuale')),
    prova_fino_al       timestamptz,
    fine_impegno        date,                       -- annuale: 12 mesi dal primo addebito, disdetta bloccata fino ad allora
    stripe_cliente      text UNIQUE,
    stripe_abbonamento  text UNIQUE,
    fine_periodo        timestamptz,                -- fin quando e' pagato (anche dopo la disdetta)
    imprese_extra       integer NOT NULL DEFAULT 0,
    sedi_extra          integer NOT NULL DEFAULT 0,
    nota                text,
    creato_il           timestamptz NOT NULL DEFAULT now(),
    aggiornato_il       timestamptz NOT NULL DEFAULT now()
);

-- Eventi ricevuti da Stripe: ogni evento si applica una volta sola (Stripe puo' rimandarli).
CREATE TABLE IF NOT EXISTS eventi_stripe (
    id          text PRIMARY KEY,
    tipo        text NOT NULL,
    ricevuto_il timestamptz NOT NULL DEFAULT now(),
    esito       text
);
