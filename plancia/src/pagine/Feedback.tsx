import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, data, NOMI_STATO_FEEDBACK, RigaFeedback, StatoFeedback } from "../api";
import { CAMPI_SCHEDA } from "../Giudizio";
import { eAdmin, useUtente } from "../utente";

// Pagina Feedback (solo amministratori): voti e segnalazioni di revisori e imprese, con lo stato e la risposta.
export default function Feedback() {
  const admin = eAdmin(useUtente());
  const [parametri, setParametri] = useSearchParams();
  const [r, setR] = useState<Awaited<ReturnType<typeof api.feedback>> | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const ricarica = () => api.feedback(Object.fromEntries(parametri)).then(setR).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, [parametri]);
  const imposta = (k: string, v: string) => {
    const p = new URLSearchParams(parametri);
    if (v) p.set(k, v); else p.delete(k);
    p.delete("pagina");
    setParametri(p);
  };
  if (errore) return <div className="allarme">{errore}</div>;
  if (!r) return <div className="caricamento">Caricamento…</div>;

  return (
    <>
      <h1>{admin ? "Feedback sulle schede" : "I miei giudizi"}</h1>
      <div className="riquadri">
        {(Object.keys(NOMI_STATO_FEEDBACK) as StatoFeedback[]).map((s) => (
          <div key={s} className="riquadro" style={{ cursor: "pointer" }} onClick={() => imposta("stato", s)}>
            <div className="etichetta">{NOMI_STATO_FEEDBACK[s]}</div><div className="numero">{r.conteggi[s] ?? 0}</div></div>))}
      </div>
      {admin ? <p className="piccolo">Le segnalazioni con problemi le rileggono gli agenti nelle sessioni (rileggono i documenti, correggono la
        scheda se hanno ragione e scrivono la risposta). Qui puoi cambiare a mano stato e risposta. I revisori pesano il doppio delle imprese.</p>
        : <p className="piccolo">I giudizi che hai dato, con lo stato e la risposta. Per dare un giudizio apri una scheda dal Catalogo
          (riquadro "Il tuo giudizio sulla scheda").</p>}
      <div className="filtri">
        <select value={parametri.get("stato") || ""} onChange={(e) => imposta("stato", e.target.value)}>
          <option value="">Tutti gli stati</option>
          {(Object.keys(NOMI_STATO_FEEDBACK) as StatoFeedback[]).map((s) => <option key={s} value={s}>{NOMI_STATO_FEEDBACK[s]}</option>)}
        </select>
        {admin && <select value={parametri.get("ruolo") || ""} onChange={(e) => imposta("ruolo", e.target.value)}>
          <option value="">Revisori, imprese e amministratori</option>
          <option value="revisore">Solo revisori</option><option value="impresa">Solo imprese</option><option value="admin">Solo amministratori</option>
        </select>}
        <select value={parametri.get("categoria") || ""} onChange={(e) => imposta("categoria", e.target.value)}>
          <option value="">Qualunque problema</option>
          {Object.entries(r.categorie).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <span className="piccolo">{r.totale} giudizi</span>
      </div>
      <table>
        <thead><tr><th>Bando</th><th>Chi</th><th>Voto</th><th>Problemi</th><th>Stato e risposta</th></tr></thead>
        <tbody>{r.feedback.map((f) => <Riga key={f.id} f={f} categorie={r.categorie} ricarica={ricarica} admin={admin} />)}</tbody>
      </table>
      <div className="pagine">
        <button disabled={r.pagina <= 1} onClick={() => imposta("pagina", String(r.pagina - 1))}>← Precedente</button>
        <span className="piccolo">pagina {r.pagina} di {Math.max(1, Math.ceil(r.totale / r.per_pagina))}</span>
        <button disabled={r.pagina * r.per_pagina >= r.totale} onClick={() => { const p = new URLSearchParams(parametri); p.set("pagina", String(r.pagina + 1)); setParametri(p); }}>Successiva →</button>
      </div>
    </>
  );
}

function Riga({ f, categorie, ricarica, admin }: { f: RigaFeedback; categorie: Record<string, string>; ricarica: () => void; admin: boolean }) {
  const [stato, setStato] = useState<StatoFeedback>(f.stato);
  const [risposta, setRisposta] = useState(f.risposta || "");
  const [errore, setErrore] = useState<string | null>(null);
  const cambiato = stato !== f.stato || risposta !== (f.risposta || "");
  const salva = async () => {
    try { await api.gestisciFeedback(f.id, { stato, risposta }); ricarica(); }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  return (
    <tr>
      <td><Link to={`/bandi/${f.bando_id}#giudizio`} className="titolo-annuncio">{f.titolo}</Link>
        <div className="piccolo">{f.ente} · versione {f.versione}{f.versione !== f.versione_attuale ? ` (ora ${f.versione_attuale})` : ""}
          {f.qualita != null ? ` · voto di Matteo ${f.qualita}` : ""}</div></td>
      <td>{f.nome || f.email}<div className="piccolo">{f.ruolo} (peso {f.peso}) · {data(f.aggiornato_il, true)}</div></td>
      <td>{f.voto ?? "–"}</td>
      <td>{f.problemi.map((p, i) => <div key={i}><b>{categorie[p.categoria] || p.categoria}</b>{p.campo ? ` (${CAMPI_SCHEDA[p.campo] || p.campo})` : ""}{p.testo ? `: ${p.testo}` : ""}</div>)}
        {f.commento && <div className="piccolo">“{f.commento}”</div>}
        {f.analisi?.regola && <div className="piccolo">Regola proposta dall'agente: {f.analisi.regola}</div>}</td>
      {!admin ? <td>{NOMI_STATO_FEEDBACK[f.stato]}{f.risposta && <div className="piccolo">{f.risposta}</div>}</td> : <td style={{ minWidth: 260 }}>
        <select value={stato} onChange={(e) => setStato(e.target.value as StatoFeedback)}>
          {(Object.keys(NOMI_STATO_FEEDBACK) as StatoFeedback[]).map((s) => <option key={s} value={s}>{NOMI_STATO_FEEDBACK[s]}</option>)}
        </select>
        <textarea rows={2} value={risposta} placeholder="risposta per chi ha scritto" onChange={(e) => setRisposta(e.target.value)} />
        {cambiato && <button onClick={salva}>Salva</button>}
        {f.gestito_da && <div className="piccolo">da {f.gestito_da}{f.gestito_il ? `, ${data(f.gestito_il, true)}` : ""}</div>}
        {errore && <div className="allarme">{errore}</div>}
      </td>}
    </tr>
  );
}
