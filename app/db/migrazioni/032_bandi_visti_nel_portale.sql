-- Email alle imprese (07/10/2026, richiesta di Matteo): nell'email entrano al massimo 10 bandi (benvenuto) o 15 (le
-- altre settimane); gli altri adatti restano nel portale. Quando l'email parte, anche questi si registrano, ma come
-- "visti nel portale" e non come inviati: non tornano come nuovi le settimane dopo e non ricevono novita' per email.
ALTER TABLE bandi_segnalati ADD COLUMN IF NOT EXISTS modo text NOT NULL DEFAULT 'email';
ALTER TABLE bandi_segnalati DROP CONSTRAINT IF EXISTS bandi_segnalati_modo;
ALTER TABLE bandi_segnalati ADD CONSTRAINT bandi_segnalati_modo CHECK (modo IN ('email', 'portale'));
