import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, data, EmailImpresa, euro, Fattura, ImpresaIscritta, NOMI_STATO_ABBONAMENTO, NOMI_STATO_RICHIESTA, RichiestaSupporto, RigaAbbonamento, StatoRichiesta } from "../api";

// Pagina Imprese (solo amministratori): richieste di supporto, email settimanali da approvare, imprese iscritte.
export default function Imprese() {
  const [richieste, setRichieste] = useState<RichiestaSupporto[]>([]);
  const [email, setEmail] = useState<EmailImpresa[]>([]);
  const [imprese, setImprese] = useState<ImpresaIscritta[]>([]);
  const [abbonamenti, setAbbonamenti] = useState<RigaAbbonamento[]>([]);
  const [fatture, setFatture] = useState<Fattura[]>([]);
  const [errore, setErrore] = useState<string | null>(null);
  const [avviso, setAvviso] = useState<string | null>(null);
  const [aperta, setAperta] = useState<number | null>(null);
  const ricarica = () => Promise.all([api.richieste().then(setRichieste), api.emailImprese().then(setEmail), api.impreseIscritte().then(setImprese), api.abbonamenti().then(setAbbonamenti), api.fatture().then(setFatture)])
    .catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, []);
  const azione = async (f: () => Promise<unknown>, testo?: string) => {
    setErrore(null); setAvviso(null);
    try { const r = await f(); if (testo) setAvviso(`${testo} ${r && typeof r === "object" ? Object.entries(r).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(", ") : ""}`); ricarica(); }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  const daApprovare = email.filter((e) => e.stato === "da_approvare");
  const decise = email.filter((e) => e.stato !== "da_approvare");

  return (
    <>
      <h1>Imprese</h1>
      {errore && <div className="allarme">{errore}</div>}
      {avviso && <div className="avviso">{avviso}</div>}

      <h2>Richieste di supporto per la domanda</h2>
      {!richieste.length ? <p className="piccolo">Nessuna richiesta.</p> : (
        <table>
          <thead><tr><th>Bando</th><th>Impresa</th><th>Messaggio</th><th>Stato e note</th></tr></thead>
          <tbody>{richieste.map((r) => <RigaRichiesta key={r.id} r={r} ricarica={ricarica} />)}</tbody>
        </table>)}

      <h2>Email settimanali da approvare</h2>
      <p className="piccolo">Il lunedì il sistema prepara un'email per ogni impresa con i bandi nuovi o in scadenza (mai due volte lo stesso
        bando). Nella fase di prova partono solo dopo la tua approvazione.{" "}
        <button onClick={() => azione(() => api.preparaEmail(), "Email della settimana:")}>Prepara adesso</button></p>
      {!daApprovare.length ? <p className="piccolo">Nessuna email in attesa.</p> : (
        <table>
          <thead><tr><th>Impresa</th><th>Oggetto</th><th>Bandi</th><th></th></tr></thead>
          <tbody>{daApprovare.map((e) => (
            <Fragment key={e.id}>
              <tr>
                <td>{e.impresa_nome}<div className="piccolo">{e.utente_email} · {e.settimana}</div></td>
                <td><a href="#" onClick={(ev) => { ev.preventDefault(); setAperta(aperta === e.id ? null : e.id); }}>{e.oggetto}</a></td>
                <td>{e.n_bandi ?? e.bandi?.length ?? "–"}</td>
                <td><button className="primario" onClick={() => azione(() => api.inviaEmail(e.id))}>Approva e invia</button>{" "}
                  <button onClick={() => azione(() => api.scartaEmail(e.id))}>Scarta</button></td>
              </tr>
              {aperta === e.id && <tr><td colSpan={4}>
                {e.html ? <iframe title="anteprima" sandbox="" srcDoc={e.html} style={{ width: "100%", height: 500, border: "1px solid var(--bordo)" }} />
                  : <pre className="testo-lungo">{e.testo}</pre>}</td></tr>}
            </Fragment>))}</tbody>
        </table>)}
      {decise.length > 0 && <details><summary className="piccolo">Ultime email decise ({decise.length})</summary>
        <table><tbody>{decise.map((e) => (
          <tr key={e.id}><td>{e.impresa_nome}</td><td>{e.oggetto}</td><td>{e.stato}{e.errore ? `: ${e.errore}` : ""}</td>
            <td className="piccolo">{e.decisa_da} {data(e.decisa_il, true)}</td></tr>))}</tbody></table></details>}

      <h2>Abbonamenti</h2>
      <p className="piccolo">Prova gratuita, abbonamenti pagati con Stripe e gratuiti (imprese amiche). Contano solo quando gli abbonamenti
        sono accesi (ABBONAMENTI_ATTIVI=1); prima entrano tutti.</p>
      {abbonamenti.length > 0 && (
        <table>
          <thead><tr><th>Utente</th><th>Stato</th><th>Imprese</th><th>Scadenze</th><th></th></tr></thead>
          <tbody>{abbonamenti.map((a) => (
            <tr key={a.utente_id}><td>{a.nome || ""} {a.email}</td>
              <td>{a.stato ? NOMI_STATO_ABBONAMENTO[a.stato] || a.stato : "non ancora entrato"}{a.piano ? ` (${a.piano})` : ""}{a.nota && <div className="piccolo">{a.nota}</div>}</td>
              <td>{a.imprese}</td>
              <td className="piccolo">{a.stato === "prova" && a.prova_fino_al ? `prova fino al ${data(a.prova_fino_al)}` : ""}
                {a.fine_impegno ? ` impegno fino al ${data(a.fine_impegno)}` : ""}</td>
              <td>{a.stato !== "gratuito" && <button onClick={() => azione(() => api.modificaAbbonamento(a.utente_id, { stato: "gratuito", nota: "gratuito impostato da Matteo" }))}>Rendi gratuito</button>}{" "}
                {(a.stato === "prova" || !a.stato) && <button onClick={() => azione(() => api.modificaAbbonamento(a.utente_id, { giorni_prova_in_piu: 14 }))}>+14 giorni di prova</button>}
                {a.stato === "gratuito" && <button onClick={() => azione(() => api.modificaAbbonamento(a.utente_id, { stato: "prova" }))}>Togli gratuito</button>}</td>
            </tr>))}</tbody>
        </table>)}

      <h2>Fatture elettroniche</h2>
      <p className="piccolo">Una per ogni pagamento riuscito su Stripe (sezionale BR), inviata allo SdI con Invoicetronic. Funziona solo
        con FATTURE_ATTIVE=1.</p>
      {fatture.length > 0 && (
        <table>
          <thead><tr><th>Numero</th><th>Cliente</th><th>Totale</th><th>Stato</th><th></th></tr></thead>
          <tbody>{fatture.map((f) => (
            <tr key={f.id}><td>{f.numero}/BR del {data(f.data)}</td><td>{f.cliente}<div className="piccolo">{f.email}</div></td>
              <td>{euro(f.totale)}<div className="piccolo">di cui IVA {euro(f.iva)}</div></td>
              <td>{f.stato}{f.esito && <div className="piccolo">{f.esito}</div>}</td>
              <td><a href={`/api/fatture/${f.id}/xml`}>XML</a>{" "}
                {f.stato === "errore" && <button onClick={() => azione(() => api.reinviaFattura(f.id))}>Rinvia</button>}{" "}
                {f.stato === "inviata" && <button onClick={() => azione(() => api.aggiornaFattura(f.id))}>Aggiorna stato</button>}</td></tr>))}</tbody>
        </table>)}

      <h2>Imprese iscritte ({imprese.length})</h2>
      <p className="piccolo">Per invitare un'impresa: pagina <Link to="/utenti">Utenti</Link>, ruolo "impresa". L'impresa poi descrive da sola
        la sua attività.</p>
      {imprese.length > 0 && (
        <table>
          <thead><tr><th>Impresa</th><th>Utente</th><th>Sedi</th><th>Email settimanale</th><th>Richieste</th><th>Iscritta</th></tr></thead>
          <tbody>{imprese.map((i) => (
            <tr key={i.id}><td>{i.nome}</td><td>{i.utente_nome || ""} {i.email}{i.attivo ? "" : " (accesso tolto)"}</td><td>{i.sedi}</td>
              <td>{i.email_settimanale ? "sì" : "no"}</td><td>{i.richieste}</td><td>{data(i.creata_il)}</td></tr>))}</tbody>
        </table>)}
    </>
  );
}

function RigaRichiesta({ r, ricarica }: { r: RichiestaSupporto; ricarica: () => void }) {
  const [stato, setStato] = useState<StatoRichiesta>(r.stato);
  const [nota, setNota] = useState(r.nota || "");
  const cambiato = stato !== r.stato || nota !== (r.nota || "");
  return (
    <tr>
      <td><Link to={`/bandi/${r.bando_id}`}>{r.bando_titolo}</Link>
        <div className="piccolo">scadenza {data(r.bando_scadenza)} · richiesta il {data(r.creata_il, true)}{r.origine === "email" ? " dall'email" : ""}</div></td>
      <td>{r.impresa_nome}<div className="piccolo">{r.utente_nome || ""} {r.email}</div></td>
      <td>{r.messaggio || "–"}</td>
      <td style={{ minWidth: 240 }}>
        <select value={stato} onChange={(e) => setStato(e.target.value as StatoRichiesta)}>
          {(Object.keys(NOMI_STATO_RICHIESTA) as StatoRichiesta[]).map((s) => <option key={s} value={s}>{NOMI_STATO_RICHIESTA[s]}</option>)}
        </select>
        <textarea rows={2} placeholder="note (le vedi solo tu)" value={nota} onChange={(e) => setNota(e.target.value)} />
        {cambiato && <button onClick={() => api.gestisciRichiesta(r.id, { stato, nota }).then(ricarica)}>Salva</button>}
      </td>
    </tr>
  );
}
