-- Le date tecniche dei passi della catena non sono una nuova versione della scheda (05/10/2026).
-- Il 04/10 un terzo delle versioni nuove (1.104 in tre giorni, senza causa) cambiava solo allegati_cercati_il,
-- stato_ricontrollato_il o pagina_cercata_il: quando il sistema ha guardato, non cosa dice il bando. Con il feedback
-- (un giudizio per utente e versione) il giudizio del revisore "scadeva" a ogni ricontrollo settimanale.
CREATE OR REPLACE FUNCTION bandi_salva_versione() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare'
                      - 'allegati_cercati_il' - 'stato_ricontrollato_il' - 'pagina_cercata_il' - 'stato_calcolato_il')
       IS DISTINCT FROM
       (to_jsonb(OLD) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare'
                      - 'allegati_cercati_il' - 'stato_ricontrollato_il' - 'pagina_cercata_il' - 'stato_calcolato_il') THEN
        INSERT INTO bandi_versioni (bando_id, versione, dati, causa)
        VALUES (OLD.id, OLD.versione, to_jsonb(OLD), nullif(current_setting('bandi_radar.causa', true), ''));
        NEW.versione := OLD.versione + 1;
        NEW.aggiornato_il := now();
    END IF;
    RETURN NEW;
END $$;
