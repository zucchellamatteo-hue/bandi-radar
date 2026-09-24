-- Registro delle notifiche gia' inviate, per non mandare due volte lo stesso riepilogo.
CREATE TABLE IF NOT EXISTS notifiche_inviate (
    nome       text NOT NULL,          -- es. novita_settimana
    chiave     text NOT NULL,          -- es. 2026-W39
    inviata_il timestamptz NOT NULL DEFAULT now(),
    esito      text NOT NULL,          -- inviata | stampata
    PRIMARY KEY (nome, chiave)
);
