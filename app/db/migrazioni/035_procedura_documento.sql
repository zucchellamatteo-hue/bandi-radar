-- Procedura nuova del regista (08/10/2026, PIANO_QUALITA azione 0, via di Matteo): prima di proporre un bando si sa
-- che tipo di agevolazione e', si verifica che il documento sia davvero il testo ufficiale giusto e si fa un secondo
-- controllo della scheda. Qui solo i dati; la regola che li usa per decidere "proponibile" e' in app/catena/procedura.py
-- e si accende con una migrazione a parte, dopo che Matteo ha visto quanti bandi cambiano.
--
--   tipo_procedura      misura_di_legge | sportello | bando (chi lo dice e quando: in verifica_documento)
--   verifica_documento  {"verificato": "si"|"no", "nome": documento ufficiale, "problema": manca | solo_sintesi |
--                        altro_bando | edizione_vecchia | bozza | atto_generico | graduatoria, "motivo",
--                        "deciso_da": sessione|ia|matteo, "deciso_il"}
--   secondo_controllo   {"esito": corretta|da_correggere|grave, "gravi": n, "minori": n, "correzioni_applicate": bool,
--                        "fatto_il", "da": sessione|ia, "cartella"}: la verifica della scheda con il testo del bando
--                        (strumenti/sessione/ar/ISTRUZIONI_VERIFICA_IA.md); vale finche' la scheda non viene rifatta
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS tipo_procedura text;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS verifica_documento jsonb;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS secondo_controllo jsonb;

-- Verifiche e controlli non sono una nuova versione della scheda (come il controllo senza IA, migrazione 026).
CREATE OR REPLACE FUNCTION bandi_salva_versione() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare'
                      - 'allegati_cercati_il' - 'stato_ricontrollato_il' - 'pagina_cercata_il' - 'stato_calcolato_il' - 'controllo'
                      - 'verifica_documento' - 'secondo_controllo')
       IS DISTINCT FROM
       (to_jsonb(OLD) - 'aggiornato_il' - 'versione' - 'qualita' - 'documentazione' - 'documentazione_motivo' - 'da_aggiornare'
                      - 'allegati_cercati_il' - 'stato_ricontrollato_il' - 'pagina_cercata_il' - 'stato_calcolato_il' - 'controllo'
                      - 'verifica_documento' - 'secondo_controllo') THEN
        INSERT INTO bandi_versioni (bando_id, versione, dati, causa)
        VALUES (OLD.id, OLD.versione, to_jsonb(OLD), nullif(current_setting('bandi_radar.causa', true), ''));
        NEW.versione := OLD.versione + 1;
        NEW.aggiornato_il := now();
    END IF;
    RETURN NEW;
END $$;
