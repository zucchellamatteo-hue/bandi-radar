import { useEffect, useState } from "react";
import { api, data, Passo } from "../api";
import { eAdmin, useUtente } from "../utente";

// Prossimi passi (05/10/2026): promemoria e lavori da fare, modificabili dall'admin. Le sessioni di Claude Code li leggono
// come elenco dei lavori da mandare in produzione.
const NUOVO = { titolo: "", dettaglio: "", tipo: "promemoria", stato: "da_fare", priorita: 2, chi: "" };
const PRIORITA: Record<number, string> = { 1: "alta", 2: "media", 3: "bassa" };

export default function Passi() {
  const admin = eAdmin(useUtente());
  const [r, setR] = useState<Awaited<ReturnType<typeof api.passi>> | null>(null);
  const [nuovo, setNuovo] = useState(NUOVO);
  const [mostraFatti, setMostraFatti] = useState(false);
  const [errore, setErrore] = useState<string | null>(null);
  const ricarica = () => api.passi().then(setR).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, []);
  const azione = async (f: () => Promise<unknown>) => {
    setErrore(null);
    try { await f(); ricarica(); } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  if (!r) return errore ? <div className="allarme">{errore}</div> : <div className="caricamento">Caricamento…</div>;
  const visibili = r.passi.filter((p) => mostraFatti || p.stato !== "fatto");
  return (
    <>
      <h1>Prossimi passi</h1>
      <p className="piccolo">Promemoria, decisioni e lavori da fare. Le sessioni di Claude Code leggono questo elenco: scrivi qui cosa vuoi
        che venga sviluppato (tipo "da sviluppare") e in che ordine (priorità).</p>
      {admin && <form className="filtri" onSubmit={(e) => { e.preventDefault(); azione(async () => { await api.creaPasso(nuovo); setNuovo(NUOVO); }); }}>
        <input type="text" placeholder="nuovo passo" value={nuovo.titolo} onChange={(e) => setNuovo({ ...nuovo, titolo: e.target.value })} required />
        <select value={nuovo.tipo} onChange={(e) => setNuovo({ ...nuovo, tipo: e.target.value })}>
          {Object.entries(r.tipi).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <select value={nuovo.priorita} onChange={(e) => setNuovo({ ...nuovo, priorita: Number(e.target.value) })}>
          {[1, 2, 3].map((n) => <option key={n} value={n}>priorità {PRIORITA[n]}</option>)}</select>
        <input type="text" placeholder="chi" value={nuovo.chi} style={{ minWidth: 100 }} onChange={(e) => setNuovo({ ...nuovo, chi: e.target.value })} />
        <button type="submit">Aggiungi</button>
      </form>}
      {errore && <div className="allarme">{errore}</div>}
      <p><label className="piccolo"><input type="checkbox" checked={mostraFatti} onChange={(e) => setMostraFatti(e.target.checked)} /> mostra anche i fatti</label></p>
      <table>
        <thead><tr><th>Passo</th><th>Tipo</th><th>Priorità</th><th>Chi</th><th>Stato</th>{admin && <th></th>}</tr></thead>
        <tbody>{visibili.map((p) => <Riga key={p.id} p={p} admin={admin} tipi={r.tipi} stati={r.stati} azione={azione} />)}</tbody>
      </table>
    </>
  );
}

function Riga({ p, admin, tipi, stati, azione }: { p: Passo; admin: boolean; tipi: Record<string, string>; stati: Record<string, string>;
  azione: (f: () => Promise<unknown>) => void }) {
  const [modifica, setModifica] = useState(false);
  const [titolo, setTitolo] = useState(p.titolo);
  const [dettaglio, setDettaglio] = useState(p.dettaglio || "");
  const cambia = (campi: Partial<Passo>) => azione(() => api.modificaPasso(p.id, campi));
  return (
    <tr style={p.stato === "fatto" ? { opacity: 0.5 } : undefined}>
      <td>{modifica ? <>
          <input type="text" value={titolo} onChange={(e) => setTitolo(e.target.value)} style={{ width: "100%" }} />
          <textarea rows={3} value={dettaglio} onChange={(e) => setDettaglio(e.target.value)} />
          <button onClick={() => { cambia({ titolo, dettaglio }); setModifica(false); }}>Salva</button>{" "}
          <button onClick={() => setModifica(false)}>Annulla</button></>
        : <><b>{p.titolo}</b>{p.dettaglio && <div className="piccolo testo-lungo">{p.dettaglio}</div>}
          <div className="piccolo">#{p.id} · aggiornato {data(p.aggiornato_il)}{p.aggiornato_da ? ` da ${p.aggiornato_da}` : ""}</div></>}</td>
      <td>{admin ? <select value={p.tipo} onChange={(e) => cambia({ tipo: e.target.value })}>
        {Object.entries(tipi).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select> : tipi[p.tipo]}</td>
      <td>{admin ? <select value={p.priorita} onChange={(e) => cambia({ priorita: Number(e.target.value) })}>
        {[1, 2, 3].map((n) => <option key={n} value={n}>{PRIORITA[n]}</option>)}</select> : PRIORITA[p.priorita]}</td>
      <td>{admin ? <input type="text" defaultValue={p.chi || ""} style={{ width: 90 }}
        onBlur={(e) => { if (e.target.value !== (p.chi || "")) cambia({ chi: e.target.value }); }} /> : p.chi}</td>
      <td>{admin ? <select value={p.stato} onChange={(e) => cambia({ stato: e.target.value })}>
        {Object.entries(stati).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select> : stati[p.stato]}</td>
      {admin && <td><button onClick={() => setModifica(!modifica)}>Modifica</button>{" "}
        <button onClick={() => { if (confirm("Cancellare questo passo?")) azione(() => api.cancellaPasso(p.id)); }}>✗</button></td>}
    </tr>
  );
}
