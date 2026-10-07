-- Blog pubblico (07/10/2026, richiesta di Matteo): brevi articoli sui bandi piu' cercati e su qualche bando di nicchia,
-- per farsi trovare da Google e dai motori di risposta IA e portare alla registrazione (app/articoli, app/pubblico/blog.py).
--
-- Un articolo nasce in bozza (chi ha il permesso "modifiche" scrive e corregge); solo l'admin lo pubblica, lo rimette in
-- bozza o lo archivia. Le pagine /blog e /blog/<slug> mostrano solo gli articoli pubblicati; quelli archiviati
-- rispondono "non piu' disponibile" (410). Se il bando collegato e' chiuso o scaduto la pagina mostra da sola il
-- riquadro "Bando chiuso" (dati dalla vista bandi_situazione), cosi' online non restano informazioni scadute.
CREATE TABLE IF NOT EXISTS articoli (
    id             bigserial PRIMARY KEY,
    titolo         text NOT NULL,
    slug           text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),   -- /blog/<slug>
    sommario       text NOT NULL,                     -- 1-2 frasi: meta description e anteprima nell'elenco
    corpo          text NOT NULL,                     -- Markdown semplice; "## Domande frequenti" + "### domanda" = FAQ
    fonti          jsonb NOT NULL DEFAULT '[]',       -- link ufficiali: [{"nome": ..., "url": "https://..."}]
    bando_id       bigint REFERENCES bandi(id) ON DELETE SET NULL,   -- facoltativo: bando di cui parla
    misura_id      text,                              -- facoltativo: id della misura nazionale (app/misure/misure.yaml)
    autore         text,                              -- vuoto = il commercialista (AUTORE_ARTICOLI nel .env)
    stato          text NOT NULL DEFAULT 'bozza' CHECK (stato IN ('bozza', 'pubblicato', 'archiviato')),
    pubblicato_il  timestamptz,                       -- prima pubblicazione (resta se lo si rimette in bozza e lo si ripubblica)
    aggiornato_il  timestamptz NOT NULL DEFAULT now(), -- ultima modifica del testo: "Aggiornato il" nella pagina
    creato_il      timestamptz NOT NULL DEFAULT now(),
    creato_da      text,
    aggiornato_da  text
);
CREATE INDEX IF NOT EXISTS articoli_stato ON articoli (stato, pubblicato_il DESC);
