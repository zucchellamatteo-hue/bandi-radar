import { useEffect, useState } from "react";
import { api, data, NOMI_RUOLO_UTENTE, RuoloUtente, Utente } from "../api";

// Pagina Utenti (solo amministratori): inviti, ruoli, accesso tolto o ridato.
export default function Utenti() {
  const [utenti, setUtenti] = useState<Utente[]>([]);
  const [email, setEmail] = useState("");
  const [nome, setNome] = useState("");
  const [ruolo, setRuolo] = useState<RuoloUtente>("revisore");
  const [esito, setEsito] = useState<{ testo: string; link?: string } | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  const ricarica = () => api.utenti().then(setUtenti).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, []);

  const spiega = (chi: string, r: { link: string; email: string }) => setEsito({
    testo: r.email === "inviata" ? `Invito mandato per email a ${chi}. Se non arriva, manda tu questo link:`
      : `L'email non è partita (servizio email non ancora attivo): manda tu questo link a ${chi}. Vale 7 giorni.`,
    link: r.link,
  });

  const invita = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrore(null); setEsito(null);
    try {
      const r = await api.creaUtente({ email, nome, ruolo });
      spiega(email, r); setEmail(""); setNome(""); ricarica();
    } catch (err) { setErrore(err instanceof Error ? err.message : String(err)); }
  };

  const azione = async (f: () => Promise<unknown>) => {
    setErrore(null); setEsito(null);
    try { await f(); ricarica(); } catch (err) { setErrore(err instanceof Error ? err.message : String(err)); }
  };

  return (
    <>
      <h1>Utenti</h1>
      <p className="piccolo">Amministratore: vede e fa tutto. Revisore: vede catalogo, schede e documenti e dà i giudizi,
        non può cambiare niente. Impresa: vede solo l'area impresa.</p>
      <form className="filtri" onSubmit={invita}>
        <input type="email" placeholder="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <input type="text" placeholder="nome (facoltativo)" value={nome} onChange={(e) => setNome(e.target.value)} style={{ minWidth: 180 }} />
        <select value={ruolo} onChange={(e) => setRuolo(e.target.value as RuoloUtente)}>
          {(Object.keys(NOMI_RUOLO_UTENTE) as RuoloUtente[]).map((r) => <option key={r} value={r}>{NOMI_RUOLO_UTENTE[r]}</option>)}
        </select>
        <button type="submit">Invita</button>
      </form>
      {errore && <div className="allarme">{errore}</div>}
      {esito && <div className="avviso">{esito.testo}{esito.link && <><br /><code className="link-invito">{esito.link}</code>{" "}
        <button type="button" onClick={() => navigator.clipboard?.writeText(esito.link!)}>Copia</button></>}</div>}
      <table>
        <thead><tr><th>Email</th><th>Nome</th><th>Ruolo</th><th>Stato</th><th>Ultimo accesso</th><th></th></tr></thead>
        <tbody>
          {utenti.map((u) => (
            <tr key={u.id} style={u.attivo ? undefined : { opacity: 0.55 }}>
              <td>{u.email}</td>
              <td>{u.nome || "–"}</td>
              <td>
                <select value={u.ruolo} disabled={!u.attivo}
                  onChange={(e) => azione(() => api.modificaUtente(u.id, { ruolo: e.target.value as RuoloUtente }))}>
                  {(Object.keys(NOMI_RUOLO_UTENTE) as RuoloUtente[]).map((r) => <option key={r} value={r}>{NOMI_RUOLO_UTENTE[r]}</option>)}
                </select>
              </td>
              <td>{!u.attivo ? "accesso tolto" : u.password_impostata ? "attivo" : "invitato, password da scegliere"}</td>
              <td>{data(u.ultimo_accesso, true)}</td>
              <td>
                {u.attivo && <button onClick={() => azione(async () => spiega(u.email, await api.reinvita(u.id)))}
                  title="Nuovo link per scegliere la password (anche se l'ha dimenticata)">Nuovo link</button>}{" "}
                <button onClick={() => azione(() => api.modificaUtente(u.id, { attivo: !u.attivo }))}>
                  {u.attivo ? "Togli accesso" : "Ridai accesso"}</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
