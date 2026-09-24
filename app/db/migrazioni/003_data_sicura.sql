-- Converte un testo in data senza far fallire la query se il testo non e' una data valida
-- (alcune API scrivono "0000-00-00" o testo libero nei campi delle scadenze).
CREATE OR REPLACE FUNCTION data_sicura(testo text) RETURNS date
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF testo IS NULL OR testo !~ '^\d{4}-\d{2}-\d{2}' OR left(testo, 4) = '0000' THEN
        RETURN NULL;
    END IF;
    RETURN left(testo, 10)::date;
EXCEPTION WHEN others THEN
    RETURN NULL;
END $$;
