-- Parte 2 del 25/09: la pagina ufficiale del bando e gli allegati scaricati da li', in ordine.
-- Migrazione aggiuntiva: nessun dato esistente cambia.

-- Esito della ricerca della pagina ufficiale (app/schede/pagina_ufficiale.py). Finche' e' 'non_trovata' il bando
-- non avra' scheda: "bando ufficiale non trovato". pagina_motivo dice da dove viene la pagina, o cosa si e' provato.
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS pagina_stato text CHECK (pagina_stato IN ('trovata', 'non_trovata'));
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS pagina_motivo text;
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS pagina_cercata_il timestamptz;
-- Quando sono stati cercati gli allegati sulla pagina ufficiale (si riazzera se la pagina cambia).
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS allegati_cercati_il timestamptz;

-- Che documento e': bando | faq | decreto | graduatoria | modulistica | pagina | altro. Decide l'ordine del testo
-- per la scheda (prima il bando, poi FAQ e ultimo decreto) e cosa resta fuori (la modulistica).
ALTER TABLE allegati ADD COLUMN IF NOT EXISTS categoria text;

-- Gli allegati trovati sulla pagina ufficiale appartengono solo al bando (annuncio_id vuoto): uno per indirizzo.
CREATE UNIQUE INDEX IF NOT EXISTS allegati_bando_url ON allegati (bando_id, url) WHERE annuncio_id IS NULL;
