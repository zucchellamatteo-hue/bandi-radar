-- Fase 1, raccolta: fonti (copia del registro YAML), controlli eseguiti, annunci trovati, pagine osservate.

-- Copia del registro fonti/*.yaml, riallineata a ogni esecuzione della raccolta.
-- Serve per collegare controlli e annunci e per la plancia (in_pausa si cambia dalla plancia, non dal YAML).
CREATE TABLE IF NOT EXISTS fonti (
    id            text PRIMARY KEY,
    nome          text NOT NULL,
    ente          text NOT NULL,
    tipo          text NOT NULL,
    territorio    text NOT NULL,
    url           text,
    modalita      text NOT NULL,
    feed_url      text,
    piattaforma   text,
    frequenza     text NOT NULL,
    stato         text NOT NULL,
    verificato_il date,
    note          text,
    in_pausa      boolean NOT NULL DEFAULT false,
    aggiornata_il timestamptz NOT NULL DEFAULT now()
);

-- Un controllo = una visita a una fonte. Esito: ok | errore | struttura_cambiata | saltato.
CREATE TABLE IF NOT EXISTS controlli (
    id             bigserial PRIMARY KEY,
    fonte_id       text NOT NULL REFERENCES fonti(id),
    iniziato_il    timestamptz NOT NULL DEFAULT now(),
    durata_ms      integer,
    esito          text NOT NULL,
    codice_http    integer,
    byte           integer,
    messaggio      text,
    elementi_letti integer NOT NULL DEFAULT 0,   -- quanti elementi (voci di feed, link, record) ha letto
    novita         integer NOT NULL DEFAULT 0    -- quanti annunci nuovi ha trovato
);
CREATE INDEX IF NOT EXISTS controlli_fonte_data ON controlli (fonte_id, iniziato_il DESC);

-- Un annuncio = un elemento trovato in una fonte (voce di feed, record API, link di una pagina).
-- Non e' ancora un bando: la Fase 3 li smista e li trasforma in schede.
CREATE TABLE IF NOT EXISTS annunci (
    id            bigserial PRIMARY KEY,
    fonte_id      text NOT NULL REFERENCES fonti(id),
    url           text NOT NULL,
    titolo        text NOT NULL,
    riassunto     text,
    pubblicato_il timestamptz,
    trovato_il    timestamptz NOT NULL DEFAULT now(),
    aggiornato_il timestamptz NOT NULL DEFAULT now(),
    impronta      text NOT NULL,                 -- hash di titolo+riassunto: cambia se l'annuncio viene modificato
    dati          jsonb,                         -- l'elemento grezzo, per le schede della Fase 3
    UNIQUE (fonte_id, url)
);
CREATE INDEX IF NOT EXISTS annunci_trovato ON annunci (trovato_il DESC);

-- Ultima lettura di ogni fonte (pagina, feed o API): impronta del contenuto e numero di elementi letti.
CREATE TABLE IF NOT EXISTS pagine (
    fonte_id      text PRIMARY KEY REFERENCES fonti(id),
    url           text NOT NULL,
    impronta      text NOT NULL,
    elementi      integer NOT NULL DEFAULT 0,    -- quanti link candidati aveva: se scende a zero, struttura cambiata
    scaricata_il  timestamptz NOT NULL DEFAULT now()
);
