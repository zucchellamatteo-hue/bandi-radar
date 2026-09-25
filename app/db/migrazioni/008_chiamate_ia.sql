-- Parte 4 del 25/09: registro delle chiamate all'IA (app/schede/ia.py), per i costi in plancia e per il tetto
-- di spesa mensile. Finche' manca la chiave API resta vuota. Migrazione aggiuntiva.
CREATE TABLE IF NOT EXISTS chiamate_ia (
    id            bigserial PRIMARY KEY,
    fatta_il      timestamptz NOT NULL DEFAULT now(),
    scopo         text NOT NULL CHECK (scopo IN ('smistamento', 'preliminare', 'scheda')),
    modello       text NOT NULL,
    batch         boolean NOT NULL DEFAULT false,      -- Batch API: meta' prezzo, risposta entro 24 ore
    batch_id      text,                                -- identificativo del lotto presso Anthropic, se batch
    riferimento   text,                                -- id degli annunci o del bando
    token_in      integer,
    token_out     integer,
    costo_usd     numeric,
    esito         text,                                -- ok | incompleta | rifiutata | errore
    messaggio     text
);
CREATE INDEX IF NOT EXISTS chiamate_ia_mese ON chiamate_ia (fatta_il);

-- Controllo preliminare con Haiku prima di Sonnet: la risposta resta sul bando.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS preliminare jsonb;
