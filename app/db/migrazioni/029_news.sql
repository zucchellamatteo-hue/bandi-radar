-- News ed email settimanale piu' ricca (07/10/2026, richiesta di Matteo).
--
-- 1. News: brevi notizie scritte da Matteo (o dalle sessioni) nella pagina "News" della plancia, senza codice.
--    Entrano nell'email del lunedi' alle imprese finche' sono pubblicate e nel periodo da/a; ogni impresa riceve la
--    stessa news una volta sola. "pubblico": imprese = solo imprese; tutti = imprese e collaboratori (Guida).
CREATE TABLE IF NOT EXISTS news (
    id             bigserial PRIMARY KEY,
    titolo         text NOT NULL,
    testo          text NOT NULL,                       -- poche righe, testo semplice
    link           text,                                -- facoltativo; "/impresa/misure" = pagina del sito
    da             date NOT NULL DEFAULT current_date,  -- periodo di pubblicazione
    a              date,                                -- vuoto = finche' non la si toglie
    pubblico       text NOT NULL DEFAULT 'imprese' CHECK (pubblico IN ('imprese', 'tutti')),
    stato          text NOT NULL DEFAULT 'bozza' CHECK (stato IN ('bozza', 'pubblicata')),
    creata_da      text,
    creata_il      timestamptz NOT NULL DEFAULT now(),
    aggiornata_il  timestamptz NOT NULL DEFAULT now(),
    aggiornata_da  text,
    CHECK (a IS NULL OR a >= da)
);

-- 2. Cosa c'e' nell'email oltre ai bandi nuovi (che restano nella colonna "bandi"): aggiornamenti sui bandi gia'
--    segnalati, news, misure nazionali nuove. Serve a non ripetere la stessa cosa due volte alla stessa impresa.
--    {"aggiornamenti": [{"bando_id", "eventi": [...], "scadenza"}], "news": [id], "misure": [id]}
ALTER TABLE email_imprese ADD COLUMN IF NOT EXISTS contenuti jsonb NOT NULL DEFAULT '{}';

-- 3. Quando un documento e' comparso la prima volta (scaricato_il cambia a ogni nuovo scaricamento): serve per dire
--    "nuove FAQ o nuova modulistica" alle imprese. I documenti gia' presenti restano senza data: non sono "nuovi".
ALTER TABLE allegati ADD COLUMN IF NOT EXISTS creato_il timestamptz;
ALTER TABLE allegati ALTER COLUMN creato_il SET DEFAULT now();

-- Prima news, in bozza: Matteo la rilegge e la pubblica dalla pagina News.
INSERT INTO news (titolo, testo, link, da, a, pubblico, stato, creata_da)
SELECT 'Novità di Bandi Radar: segnalazioni, smartphone e agevolazioni nazionali',
       'Da questa settimana in ogni pagina c''è il pulsante "Segnala": se un bando manca, una scadenza è sbagliata o '
       || 'qualcosa non torna, scrivicelo in due righe e lo controlliamo. Bandi Radar ora si usa comodamente anche dallo '
       || 'smartphone. Nella sezione "Agevolazioni fiscali" trovi nuove misure nazionali, con esempi pratici per tipo di '
       || 'impresa: incentivi alle assunzioni 2026 (Bonus Giovani, Bonus Donne, Bonus ZES), maxi-deduzione del costo dei '
       || 'nuovi assunti, Fondo di Garanzia per le PMI, Ecobonus e Sismabonus per gli immobili dell''impresa, Art Bonus.',
       '/impresa/misure', DATE '2026-10-12', DATE '2026-10-25', 'imprese', 'bozza', 'Claude (sessione del 07/10)'
WHERE NOT EXISTS (SELECT 1 FROM news);
