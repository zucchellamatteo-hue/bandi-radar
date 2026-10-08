import { useState } from "react";
import { api, NOMI_RUOLO_UTENTE } from "../api";
import { useUtente } from "../utente";

// Il mio account (05/10/2026): scaricare i propri dati e cancellare l'account (GDPR).
export default function Account() {
  const u = useUtente();
  const [password, setPassword] = useState("");
  const [conferma, setConferma] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  if (!u) return null;
  const cancella = async () => {
    setErrore(null);
    try { await api.cancellaAccount(password); window.location.href = "/"; }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  return (
    <>
      <h1>Il mio account</h1>
      <p><b>{u.nome || u.email}</b> · {u.email} · {NOMI_RUOLO_UTENTE[u.ruolo]}</p>
      <h2>I miei dati</h2>
      <p>Scarica in un file tutti i dati che bandinQiaro conserva su di te: account, imprese e profili, richieste di supporto,
        giudizi, abbonamento, dati di fatturazione, accessi recenti. La password non c'è: la salviamo solo in forma cifrata.</p>
      <p><a href="/api/account/dati"><button>Scarica i miei dati</button></a></p>
      <h2>Cancellare l'account</h2>
      {u.ruolo === "admin" ? <p className="piccolo">Un amministratore non può cancellarsi da qui: un altro amministratore può togliergli
        l'accesso dalla pagina Utenti.</p> : <>
        <p>Si cancellano l'account, le imprese con i loro profili, le richieste, i giudizi e i dati di fatturazione. Restano solo le
          eventuali fatture già emesse, che la legge impone di conservare per 10 anni. Non si può annullare.</p>
        {!conferma ? <button onClick={() => setConferma(true)}>Voglio cancellare il mio account</button> : (
          <div className="allarme">
            <p>Per confermare scrivi la tua password.</p>
            <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />{" "}
            <button onClick={cancella} disabled={!password}>Cancella definitivamente</button>{" "}
            <button onClick={() => { setConferma(false); setPassword(""); }}>Annulla</button>
            {errore && <p><b>{errore}</b></p>}
          </div>)}
      </>}
    </>
  );
}
