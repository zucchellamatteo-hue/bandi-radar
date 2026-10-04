-- Utenti e accesso (05/10/2026, prodotto indipendente): al posto dell'unico utente del .env (autenticazione base).
-- Ruoli: admin (Matteo e collaboratori, tutto), revisore (catalogo, schede, documenti, feedback; nessuna modifica),
-- impresa (solo l'area impresa). I dati identificativi stanno qui, separati dai profili usati per l'abbinamento:
-- all'IA non arriva mai nulla di queste tabelle.
CREATE TABLE IF NOT EXISTS utenti (
    id             bigserial PRIMARY KEY,
    email          text NOT NULL,                       -- minuscolo; il primo admin puo' avere il nome utente del .env
    nome           text,
    ruolo          text NOT NULL CHECK (ruolo IN ('admin', 'revisore', 'impresa')),
    password_hash  text,                                -- NULL finche' l'invitato non sceglie la password
    attivo         boolean NOT NULL DEFAULT true,
    creato_il      timestamptz NOT NULL DEFAULT now(),
    creato_da      bigint REFERENCES utenti(id) ON DELETE SET NULL,
    ultimo_accesso timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS utenti_email ON utenti (lower(email));

-- Sessioni del browser: nel cookie va un codice casuale, qui se ne salva solo l'impronta (sha256).
CREATE TABLE IF NOT EXISTS sessioni (
    impronta   text PRIMARY KEY,
    utente_id  bigint NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
    creata_il  timestamptz NOT NULL DEFAULT now(),
    scade_il   timestamptz NOT NULL,
    ultimo_uso timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sessioni_utente ON sessioni (utente_id);

-- Link mandati per email: invito (scegli la password), recupero password, conferma dell'indirizzo.
-- Come per le sessioni, si salva solo l'impronta; ogni link vale una volta sola.
CREATE TABLE IF NOT EXISTS link_email (
    impronta  text PRIMARY KEY,
    utente_id bigint NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
    scopo     text NOT NULL CHECK (scopo IN ('invito', 'recupero', 'conferma')),
    creato_il timestamptz NOT NULL DEFAULT now(),
    scade_il  timestamptz NOT NULL,
    usato_il  timestamptz
);

-- Tentativi di accesso, per fermare chi prova password a ripetizione (5 errori = pausa di 15 minuti).
CREATE TABLE IF NOT EXISTS tentativi_accesso (
    id       bigserial PRIMARY KEY,
    email    text NOT NULL,
    ip       text,
    riuscito boolean NOT NULL,
    quando   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS tentativi_accesso_email ON tentativi_accesso (lower(email), quando);
CREATE INDEX IF NOT EXISTS tentativi_accesso_ip ON tentativi_accesso (ip, quando);
