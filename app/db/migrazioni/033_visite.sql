-- Statistiche delle pagine pubbliche senza cookie (08/10/2026, richiesta di Matteo per misurare SEO e GEO).
-- Solo contatori aggregati per giorno: NIENTE indirizzi IP, User-Agent completi, cookie o altri identificativi.
-- Una riga per giorno e combinazione; ogni visita a /, /blog, /blog/<slug>, /llms.txt, /sitemap.xml o /robots.txt
-- aumenta "conteggio" di 1 (app/visite). Le pagine della plancia e chi ha fatto l'accesso non si contano.
CREATE TABLE IF NOT EXISTS visite (
    giorno        date NOT NULL DEFAULT current_date,
    percorso      text NOT NULL,                       -- es. /blog/nuova-sabatini
    provenienza   text NOT NULL DEFAULT 'diretto',     -- solo il dominio del Referer (google.it, chatgpt.com), "diretto", "interno"
    utm_source    text NOT NULL DEFAULT '',
    utm_medium    text NOT NULL DEFAULT '',
    utm_campaign  text NOT NULL DEFAULT '',
    visitatore    text NOT NULL CHECK (visitatore IN ('persona', 'motore', 'ia', 'altro')),
    programma     text NOT NULL DEFAULT '',            -- nome del programma (Googlebot, GPTBot...); vuoto per le persone
    conteggio     integer NOT NULL DEFAULT 0,
    PRIMARY KEY (giorno, percorso, provenienza, utm_source, utm_medium, utm_campaign, visitatore, programma)
);
