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
        {" · "}<a href="/registrati">Sei un'impresa? Registrati</a>
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

// Registrazione di un'impresa (solo se aperta: REGISTRAZIONE_APERTA=1); l'accesso arriva con il link di conferma.
export function Registrati() {
  const [aperta, setAperta] = useState<boolean | null>(null);
  const [email, setEmail] = useState("");
  const [nome, setNome] = useState("");
  const [password, setPassword] = useState("");
  const [messaggio, setMessaggio] = useState<string | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { api.statoRegistrazione().then((r) => setAperta(r.aperta)).catch(() => setAperta(false)); }, []);
  const invia = async (e: React.FormEvent) => {
    e.preventDefault(); setErrore(null);
    try { setMessaggio((await api.registrati({ email, password, nome })).messaggio); }
    catch (err) { setErrore(err instanceof Error ? err.message : String(err)); }
  };
  return (
    <div className="accesso">
      <div className="logo-accesso">Bandi Radar</div>
      <p className="piccolo">I bandi per la tua impresa, ogni settimana.</p>
      {aperta === false && <div className="avviso">Le registrazioni non sono ancora aperte: scrivici per avere un invito.</div>}
      {messaggio ? <div className="avviso">{messaggio}</div> : aperta && (
        <form onSubmit={invia}>
          <label>Il tuo nome<input type="text" autoComplete="name" value={nome} onChange={(e) => setNome(e.target.value)} /></label>
          <label>Email<input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
          <label>Password (almeno 10 caratteri)<input type="password" autoComplete="new-password" required minLength={10} value={password}
            onChange={(e) => setPassword(e.target.value)} /></label>
          {errore && <div className="allarme">{errore}</div>}
          <button type="submit" className="primario">Registrati</button>
        </form>)}
      <p className="piccolo"><a href="/">Hai già un account? Entra</a></p>
    </div>
  );
}

// Link di conferma dell'indirizzo: conferma ed entra.
export function ConfermaEmail({ entrato }: { entrato: (u: Utente) => void }) {
  const [parametri] = useSearchParams();
  const vai = useNavigate();
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => {
    api.confermaEmail(parametri.get("codice") || "").then((u) => { entrato(u); vai("/", { replace: true }); })
      .catch((e) => setErrore(String(e.message || e)));
  }, []);
  return (
    <div className="accesso">
      <div className="logo-accesso">Bandi Radar</div>
      {errore ? <><div className="allarme">{errore}</div><p><a href="/">Vai all'accesso</a></p></> : <p>Confermo l'indirizzo…</p>}
    </div>
  );
}

// Link "non voglio più l'email" (senza accesso).
export function Disiscrizione() {
  const [parametri] = useSearchParams();
  const [esito, setEsito] = useState<string | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => {
    api.disiscrivi(parametri.get("codice") || "").then((r) => setEsito(r.impresa)).catch((e) => setErrore(String(e.message || e)));
  }, []);
  return (
    <div className="accesso">
      <div className="logo-accesso">Bandi Radar</div>
      {esito ? <p>Fatto: <b>{esito}</b> non riceverà più l'email settimanale. Puoi riattivarla quando vuoi dalla pagina
        "Le mie imprese".</p> : errore ? <div className="allarme">Link non valido.</div> : <p>Un momento…</p>}
      <p className="piccolo"><a href="/">Vai a Bandi Radar</a></p>
    </div>
  );
}
