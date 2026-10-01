-- Filtro senza IA (01/10/2026, richiesta di Matteo): il bando ha tra i documenti scaricati il testo ufficiale?
-- 'bando' = almeno un documento (PDF, Word...) che si legge come un regolamento; 'sintesi' = solo pagine o notizie;
-- 'nessuno' = niente di leggibile. Solo i bandi 'bando' vanno alla scheda (app/schede/documentazione.py).
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS documentazione text
    CHECK (documentazione IN ('bando', 'sintesi', 'nessuno'));
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS documentazione_motivo text;
CREATE INDEX IF NOT EXISTS bandi_documentazione ON bandi (documentazione);

-- Il risultato del filtro non e' una nuova versione della scheda (come il voto di Matteo).
CREATE OR REPLACE FUNCTION bandi_salva_versione() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo')
       IS DISTINCT FROM (to_jsonb(OLD) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo') THEN
        INSERT INTO bandi_versioni (bando_id, versione, dati, causa)
        VALUES (OLD.id, OLD.versione, to_jsonb(OLD), nullif(current_setting('bandi_radar.causa', true), ''));
        NEW.versione := OLD.versione + 1;
        NEW.aggiornato_il := now();
    END IF;
    RETURN NEW;
END $$;
