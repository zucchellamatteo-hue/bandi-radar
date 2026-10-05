-- Bandi uniti (06/10/2026): quando gli annunci di un bando gia' schedato passano a un altro bando (doppione), il
-- bando vuoto non si cancella (la scheda resta come storico) ma si segna "unito a": catalogo, ricontrolli e
-- aggiornamenti delle schede lo ignorano, la sua pagina rimanda al bando principale.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS unito_a bigint REFERENCES bandi(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS bandi_unito_a ON bandi (unito_a) WHERE unito_a IS NOT NULL;
-- I quattro doppioni uniti il 05/10/2026 (stesso url_chiave e stessi documenti).
UPDATE bandi SET unito_a = v.principale FROM (VALUES (1931, 1930), (2406, 2402), (4202, 4198), (4043, 979)) AS v(doppione, principale)
 WHERE bandi.id = v.doppione AND EXISTS (SELECT 1 FROM bandi p WHERE p.id = v.principale)
   AND NOT EXISTS (SELECT 1 FROM annunci a WHERE a.bando_id = bandi.id);
