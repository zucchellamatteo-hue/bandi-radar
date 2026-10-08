-- Fattura elettronica (05/10/2026): dati di fatturazione dei clienti e fatture emesse per gli abbonamenti pagati.
-- L'XML FatturaPA lo genera bandinQiaro (app/fatture), l'invio allo SdI lo fa Invoicetronic; la conservazione a norma
-- e' quella gratuita dell'Agenzia delle Entrate. Tabelle separate dai profili: all'IA non arriva niente di qui.
CREATE TABLE IF NOT EXISTS dati_fatturazione (
    utente_id           bigint PRIMARY KEY REFERENCES utenti(id) ON DELETE CASCADE,
    denominazione       text NOT NULL,
    partita_iva         text NOT NULL,
    codice_fiscale      text,
    codice_destinatario text,                      -- 7 caratteri; '0000000' se c'e' solo la PEC
    pec                 text,
    indirizzo           text NOT NULL,
    cap                 text NOT NULL,
    comune              text NOT NULL,
    provincia           text NOT NULL,
    aggiornato_il       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fatture (
    id              bigserial PRIMARY KEY,
    anno            integer NOT NULL,
    numero          integer NOT NULL,              -- progressivo dell'anno, sezionale "BR" (separato dallo studio)
    utente_id       bigint REFERENCES utenti(id) ON DELETE SET NULL,
    stripe_fattura  text UNIQUE,                   -- una fattura per pagamento Stripe, mai due
    data            date NOT NULL,
    cliente         jsonb NOT NULL,                -- dati di fatturazione al momento dell'emissione
    righe           jsonb NOT NULL,
    imponibile      numeric(12, 2) NOT NULL,
    iva             numeric(12, 2) NOT NULL,
    totale          numeric(12, 2) NOT NULL,
    xml             text NOT NULL,
    stato           text NOT NULL DEFAULT 'da_inviare'
                    CHECK (stato IN ('da_inviare', 'inviata', 'consegnata', 'non_consegnata', 'scartata', 'errore')),
    invio_id        text,                          -- id dell'invio presso Invoicetronic
    esito           text,                          -- ultima notifica o errore, leggibile
    creata_il       timestamptz NOT NULL DEFAULT now(),
    aggiornata_il   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (anno, numero)
);
