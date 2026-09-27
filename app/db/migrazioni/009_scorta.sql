-- Lettura della "scorta" (27/09/2026, valutazione dell'efficacia): oltre al controllo delle novita', le fonti con
-- il blocco `scorta` nel registro vengono lette per intero (tutte le pagine) la prima volta e poi una volta al mese.

-- Un controllo e' una lettura normale ('novita') o completa ('scorta').
ALTER TABLE controlli ADD COLUMN IF NOT EXISTS tipo text NOT NULL DEFAULT 'novita';

-- Un annuncio trovato leggendo la scorta e' un bando gia' pubblicato, non una novita': non entra nel riepilogo
-- del lunedi', nella pagina Novita' e nei conteggi delle novita' della plancia.
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS da_scorta boolean NOT NULL DEFAULT false;

-- Date di pubblicazione nel futuro (Camera di Caserta: tutte al 30/10/2026, cioe' la scadenza di un bando letta
-- nell'elenco): si spostano nei dati grezzi come data_futura e la pubblicazione resta vuota. Da ora lo fa la raccolta.
UPDATE annunci
SET dati = coalesce(dati, '{}'::jsonb) || jsonb_build_object('data_futura', to_char(pubblicato_il, 'YYYY-MM-DD')),
    pubblicato_il = NULL
WHERE pubblicato_il > trovato_il + interval '1 day';
