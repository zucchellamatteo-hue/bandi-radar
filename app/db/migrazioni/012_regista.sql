-- Regista della fase 2 (01/10/2026, richiesta di Matteo): app/catena/regista.py decide ogni ora i passi su annunci e
-- bandi, riprova quelli fermi, sblocca i dubbi e chiede l'aggiornamento delle schede. Vedi docs/ORCHESTRAZIONE.md.

-- I doppioni dubbi li decidono anche le regole (titoli quasi uguali dello stesso ente, titoli poco simili).
ALTER TABLE bandi_dubbi DROP CONSTRAINT IF EXISTS bandi_dubbi_deciso_da_check;
ALTER TABLE bandi_dubbi ADD CONSTRAINT bandi_dubbi_deciso_da_check CHECK (deciso_da IN ('regole', 'ia', 'matteo'));

-- L'IA decide anche i doppioni "simili" (somiglianza 0,7-0,9).
ALTER TABLE chiamate_ia DROP CONSTRAINT IF EXISTS chiamate_ia_scopo_check;
ALTER TABLE chiamate_ia ADD CONSTRAINT chiamate_ia_scopo_check
    CHECK (scopo IN ('smistamento', 'preliminare', 'scheda', 'doppione'));

-- Quando e' stata fatta la scheda, e perche' va rifatta (nuovi documenti, proroga, rettifica, chiusura).
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS scheda_il timestamptz;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS da_aggiornare text;
UPDATE bandi SET scheda_il = aggiornato_il WHERE dati IS NOT NULL AND scheda_il IS NULL;

-- Ogni azione del regista, per la pagina Lavorazione della plancia.
CREATE TABLE IF NOT EXISTS eventi_catena (
    id          bigserial PRIMARY KEY,
    quando      timestamptz NOT NULL DEFAULT now(),
    oggetto     text NOT NULL CHECK (oggetto IN ('annuncio', 'bando', 'giro')),
    oggetto_id  bigint,
    passo       text NOT NULL,
    esito       text NOT NULL,
    motivo      text
);
CREATE INDEX IF NOT EXISTS eventi_catena_oggetto ON eventi_catena (oggetto, oggetto_id);
CREATE INDEX IF NOT EXISTS eventi_catena_quando ON eventi_catena (quando DESC);

-- "Da aggiornare" non e' una nuova versione della scheda (come il voto e il filtro dei documenti).
CREATE OR REPLACE FUNCTION bandi_salva_versione() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare')
       IS DISTINCT FROM
       (to_jsonb(OLD) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare') THEN
        INSERT INTO bandi_versioni (bando_id, versione, dati, causa)
        VALUES (OLD.id, OLD.versione, to_jsonb(OLD), nullif(current_setting('bandi_radar.causa', true), ''));
        NEW.versione := OLD.versione + 1;
        NEW.aggiornato_il := now();
    END IF;
    RETURN NEW;
END $$;
