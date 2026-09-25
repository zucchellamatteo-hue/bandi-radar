-- Parte 1 del 25/09: annuncio e bando separati. Un bando ha molti annunci (lo stesso bando da piu' fonti,
-- proroghe, rettifiche, graduatorie, FAQ); gli allegati appartengono al bando.
-- Migrazione aggiuntiva: nessun dato esistente si perde (annunci, smistamenti, allegati, correzioni di Matteo).

-- Un bando non e' piu' "un annuncio": annuncio_id resta come annuncio di origine, ma non e' piu' unico.
ALTER TABLE bandi DROP CONSTRAINT IF EXISTS bandi_annuncio_id_key;

-- Chiavi per riconoscere i doppioni (app/schede/bandi.py), dalla piu' affidabile:
--   codice_ufficiale: il codice del bando quando l'ente ne da' uno (Lombardia: RLO12026055023);
--   url_chiave: indirizzo della pagina ufficiale ripulito (senza http, www, / finale, parametri di tracciamento);
--   chiave_titolo: ente + edizione (anni, "secondo sportello") + parole del titolo, normalizzati.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS codice_ufficiale text;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS url_chiave text;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS chiave_titolo text;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS versione integer NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS bandi_codice ON bandi (codice_ufficiale);

-- Il legame annuncio -> bando, con il ruolo dell'annuncio per quel bando.
-- collegato_da: chi ha deciso il legame. Quello di Matteo non si tocca mai (come per lo smistamento).
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS bando_id bigint REFERENCES bandi(id) ON DELETE SET NULL;
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS ruolo text
    CHECK (ruolo IN ('origine', 'doppione', 'proroga', 'rettifica', 'graduatoria', 'faq', 'chiusura'));
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS collegato_da text CHECK (collegato_da IN ('regole', 'ia', 'matteo'));
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS collegato_il timestamptz;
ALTER TABLE annunci ADD COLUMN IF NOT EXISTS collegamento_motivo text;
CREATE INDEX IF NOT EXISTS annunci_bando ON annunci (bando_id);

-- Travaso: le eventuali schede gia' create (una per annuncio) diventano il bando "di origine" del loro annuncio.
UPDATE annunci a SET bando_id = b.id, ruolo = 'origine', collegato_da = 'regole', collegato_il = now(),
       collegamento_motivo = 'scheda creata prima della separazione annuncio/bando'
FROM bandi b WHERE b.annuncio_id = a.id AND a.bando_id IS NULL;

-- Gli allegati appartengono al bando. annuncio_id resta (da quale pagina e' arrivato il file) ma puo' mancare
-- per i documenti trovati sulla pagina ufficiale del bando.
ALTER TABLE allegati ALTER COLUMN annuncio_id DROP NOT NULL;
UPDATE allegati al SET bando_id = a.bando_id FROM annunci a
WHERE al.annuncio_id = a.id AND al.bando_id IS NULL AND a.bando_id IS NOT NULL;

-- Storico minimo: a ogni modifica di una scheda si conserva la versione precedente, intera.
-- La "causa" (per esempio "annuncio 123, proroga") la imposta chi modifica, con
-- SELECT set_config('bandi_radar.causa', '...', true) nella stessa transazione.
CREATE TABLE IF NOT EXISTS bandi_versioni (
    id          bigserial PRIMARY KEY,
    bando_id    bigint NOT NULL REFERENCES bandi(id) ON DELETE CASCADE,
    versione    integer NOT NULL,                  -- il numero della versione conservata
    dati        jsonb NOT NULL,                    -- la riga di bandi com'era prima della modifica
    causa       text,
    salvata_il  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS bandi_versioni_bando ON bandi_versioni (bando_id, versione);

CREATE OR REPLACE FUNCTION bandi_salva_versione() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- Il voto di Matteo e le date tecniche non sono una nuova versione della scheda.
    IF (to_jsonb(NEW) - 'aggiornato_il' - 'versione' - 'qualita')
       IS DISTINCT FROM (to_jsonb(OLD) - 'aggiornato_il' - 'versione' - 'qualita') THEN
        INSERT INTO bandi_versioni (bando_id, versione, dati, causa)
        VALUES (OLD.id, OLD.versione, to_jsonb(OLD), nullif(current_setting('bandi_radar.causa', true), ''));
        NEW.versione := OLD.versione + 1;
        NEW.aggiornato_il := now();
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS bandi_versione ON bandi;
CREATE TRIGGER bandi_versione BEFORE UPDATE ON bandi FOR EACH ROW EXECUTE FUNCTION bandi_salva_versione();

-- Doppioni dubbi: l'annuncio somiglia a un bando esistente ma le regole non sono sicure.
-- Resta senza bando finche' qualcuno decide: oggi Matteo dalla plancia, piu' avanti Haiku.
-- bando_id vuoto = aggiornamento (proroga, graduatoria...) di cui non si e' trovato il bando.
CREATE TABLE IF NOT EXISTS bandi_dubbi (
    id           bigserial PRIMARY KEY,
    annuncio_id  bigint NOT NULL REFERENCES annunci(id) ON DELETE CASCADE,
    bando_id     bigint REFERENCES bandi(id) ON DELETE CASCADE,
    somiglianza  numeric,                          -- 0-1, quanto si somigliano i titoli
    motivo       text,
    creato_il    timestamptz NOT NULL DEFAULT now(),
    decisione    text CHECK (decisione IN ('stesso', 'diverso')),
    deciso_da    text CHECK (deciso_da IN ('ia', 'matteo')),
    deciso_il    timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS bandi_dubbi_coppia ON bandi_dubbi (annuncio_id, coalesce(bando_id, 0));
CREATE INDEX IF NOT EXISTS bandi_dubbi_aperti ON bandi_dubbi (annuncio_id) WHERE decisione IS NULL;
