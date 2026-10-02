-- Forma dell'incentivo (richiesta di Matteo del 02/10/2026): fondo perduto, finanziamento agevolato, servizi...
-- con quota sulla spesa e massimale, una riga per gruppo di beneficiari o linea (struttura in app/schede/ia.py).
-- Le schede scritte prima non ce l'hanno: la plancia la ricava dai campi esistenti (app/schede/forma_incentivo.py)
-- e la segna come "ricavata", finche' una sessione o l'API non la compilano dai documenti.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS forma_incentivo jsonb;
