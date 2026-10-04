import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, Utente } from "../api";

// Pagina di accesso: email e password, oppure richiesta del link per una password nuova.
export function Accesso({ entrato }: { entrato: (u: Utente) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [recupero, setRecupero] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  const [messaggio, setMessaggio] = useState<string | null>(null);
  const [inCorso, setInCorso] = useState(false);

  const invia = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrore(null); setMessaggio(null); setInCorso(true);
    try {
      if (recupero) setMessaggio((await api.recupero(email)).messaggio);
      else entrato(await api.entra(email, password));
    } catch (err) { setErrore(err instanceof Error ? err.message : String(err)); }
    setInCorso(false);
  };

  return (
    <div className="accesso">
      <div className="logo-accesso">Bandi Radar</div>
      <p className="piccolo">Finanza agevolata per le imprese</p>
      <form onSubmit={invia}>
        <label>Email<input type="text" inputMode="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        {!recupero && <label>Password<input type="password" autoComplete="current-password" required value={password}
          onChange={(e) => setPassword(e.target.value)} /></label>}
        {errore && <div className="allarme">{errore}</div>}
        {messaggio && <div className="avviso">{messaggio}</div>}
        <button type="submit" className="primario" disabled={inCorso}>{recupero ? "Mandami il link" : "Entra"}</button>
      </form>
      <p className="piccolo">
        <a href="#" onClick={(e) => { e.preventDefault(); setRecupero(!recupero); setErrore(null); setMessaggio(null); }}>
          {recupero ? "← Torna all'accesso" : "Password dimenticata?"}</a>
      </p>
    </div>
  );
}

// Pagina del link ricevuto per email (invito o recupero): si sceglie la password e si entra.
export function ImpostaPassword({ entrato }: { entrato: (u: Utente) => void }) {
  const [parametri] = useSearchParams();
  const vai = useNavigate();
  const codice = parametri.get("codice") || "";
  const [chi, setChi] = useState<{ email: string; nome: string | null; scopo: string } | null>(null);
  const [password, setPassword] = useState("");
  const [ripeti, setRipeti] = useState("");
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => { api.controllaLink(codice).then(setChi).catch((e) => setErrore(String(e.message || e))); }, [codice]);

  const invia = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrore(null);
    if (password !== ripeti) { setErrore("Le due password non coincidono."); return; }
    try {
      const u = await api.impostaPassword(codice, password);
      entrato(u);
      vai("/", { replace: true });
    } catch (err) { setErrore(err instanceof Error ? err.message : String(err)); }
  };

  return (
    <div className="accesso">
      <div className="logo-accesso">Bandi Radar</div>
      {chi && <p>{chi.scopo === "invito" ? "Benvenuto" : "Nuova password per"} <strong>{chi.nome || chi.email}</strong></p>}
      {chi ? (
        <form onSubmit={invia}>
          <input type="email" autoComplete="username" value={chi.email} readOnly hidden />
          <label>Scegli una password (almeno 10 caratteri)
            <input type="password" autoComplete="new-password" required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
          <label>Ripetila<input type="password" autoComplete="new-password" required value={ripeti} onChange={(e) => setRipeti(e.target.value)} /></label>
          {errore && <div className="allarme">{errore}</div>}
          <button type="submit" className="primario">Salva ed entra</button>
        </form>
      ) : errore ? <><div className="allarme">{errore}</div><p><a href="/">Vai all'accesso</a></p></> : <p>Controllo il link…</p>}
    </div>
  );
}
