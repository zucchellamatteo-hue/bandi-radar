-- Profili d'impresa ANONIMI (Fase 4, anticipata il 29/09/2026): solo un codice scelto da Matteo e i dati che servono
-- all'abbinamento. Niente nomi, codici fiscali, partite IVA, email. Formato in docs/PROFILO_IMPRESA.md, controlli in
-- app/abbinamento/profilo.py. Lo stesso formato arrivera' da Qiaro / Contract to Cash via API.
CREATE TABLE IF NOT EXISTS profili (
    id            bigserial PRIMARY KEY,
    codice        text NOT NULL UNIQUE CHECK (codice ~ '^[A-Za-z0-9._-]{1,40}$'),
    profilo       jsonb NOT NULL,
    origine       text NOT NULL DEFAULT 'plancia',     -- plancia (Matteo a mano), anagrafiche, qiaro
    creato_il     timestamptz NOT NULL DEFAULT now(),
    aggiornato_il timestamptz NOT NULL DEFAULT now()
);
