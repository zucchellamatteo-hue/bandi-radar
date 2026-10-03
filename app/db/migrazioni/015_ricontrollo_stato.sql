-- Ricontrollo settimanale dello stato dei bandi proponibili (piano del 03/10/2026, punto 1): quando il regista ha
-- riscaricato l'ultima volta la pagina ufficiale per cercare avvisi di chiusura (app/schede/ricontrollo_stato.py).
ALTER TABLE bandi ADD COLUMN IF NOT EXISTS stato_ricontrollato_il timestamptz;
