-- Feedback sulle schede (05/10/2026, tappa 2 del prodotto indipendente): voto 1-5 ("mi fiderei per proporlo?") e
-- problemi segnalati da revisori e imprese. Una riga per utente e versione della scheda (si puo' cambiare).
-- Gli agenti delle sessioni rileggono i documenti e decidono (strumenti/sessione/ar/esporta_feedback.py): l'esito va
-- in `analisi`, le correzioni accettate cambiano la scheda con la causa "feedback N" nello storico delle versioni.
-- Il voto di Matteo in bandi.qualita resta com'e'.
CREATE TABLE IF NOT EXISTS feedback (
    id            bigserial PRIMARY KEY,
    bando_id      bigint NOT NULL REFERENCES bandi(id) ON DELETE CASCADE,
    versione      integer NOT NULL,                       -- versione della scheda giudicata
    utente_id     bigint NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
    ruolo         text NOT NULL,                          -- ruolo di chi scrive quando scrive: i revisori pesano di piu'
    voto          smallint CHECK (voto BETWEEN 1 AND 5),
    problemi      jsonb NOT NULL DEFAULT '[]',            -- [{categoria, campo, testo}]
    commento      text,
    stato         text NOT NULL DEFAULT 'nuovo' CHECK (stato IN ('nuovo', 'preso_in_carico', 'corretto', 'respinto')),
    risposta      text,                                   -- spiegazione per chi ha scritto (correzione o motivo del no)
    analisi       jsonb,                                  -- esito dell'agente: per problema ha_ragione, correzioni, regola
    creato_il     timestamptz NOT NULL DEFAULT now(),
    aggiornato_il timestamptz NOT NULL DEFAULT now(),
    gestito_il    timestamptz,
    gestito_da    text,                                   -- email dell'admin o "agente"
    UNIQUE (bando_id, versione, utente_id)
);
CREATE INDEX IF NOT EXISTS feedback_stato ON feedback (stato, creato_il);
CREATE INDEX IF NOT EXISTS feedback_bando ON feedback (bando_id);
