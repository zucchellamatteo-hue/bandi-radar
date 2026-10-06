-- Controllo delle schede senza IA (06/10/2026, richiesta di Matteo): il regista ricontrolla ogni scheda nuova o
-- aggiornata e salva qui i problemi trovati (app/schede/controlli.py). Le schede con problemi gravi non si propongono
-- alle imprese finche' non sono sistemate; tutte compaiono in "Da rivedere" nella pagina Lavorazione.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS controllo jsonb;   -- {"fatto_il", "gravi": [...], "da_migliorare": [...]}

-- Il controllo non e' una nuova versione della scheda (come le altre date tecniche, migrazione 018).
CREATE OR REPLACE FUNCTION bandi_salva_versione() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare'
                      - 'allegati_cercati_il' - 'stato_ricontrollato_il' - 'pagina_cercata_il' - 'stato_calcolato_il' - 'controllo')
       IS DISTINCT FROM
       (to_jsonb(OLD) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare'
                      - 'allegati_cercati_il' - 'stato_ricontrollato_il' - 'pagina_cercata_il' - 'stato_calcolato_il' - 'controllo') THEN
        INSERT INTO bandi_versioni (bando_id, versione, dati, causa)
        VALUES (OLD.id, OLD.versione, to_jsonb(OLD), nullif(current_setting('bandi_radar.causa', true), ''));
        NEW.versione := OLD.versione + 1;
        NEW.aggiornato_il := now();
    END IF;
    RETURN NEW;
END $$;
