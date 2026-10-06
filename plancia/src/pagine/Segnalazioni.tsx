import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, data, Segnalazione, StatoSegnalazione, TipoSegnalazione } from "../api";
import { usePuo } from "../utente";

// Pagina Segnalazioni (06/10): quello che arriva dal pulsante "Segnala". La vede chi ha il permesso "lavoro"; chi ha
// "modifiche" le chiude con uno stato e una risposta. Le sessioni di Claude le leggono con python -m app.segnalazioni.
export default function Segnalazioni() {
  const gestisce = usePuo("modifiche");
  const [parametri, setParametri] = useSearchParams();
  const [r, setR] = useState<Awaited<ReturnType<typeof api.segnalazioni>> | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const filtri = Object.fromEntries(parametri);
  if (!("stato" in filtri)) filtri.stato = "aperte";     // all'apertura: solo quelle da guardare
  const ricarica = () => api.segnalazioni(filtri).then(setR).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, [parametri]);
  const imposta = (k: string, v: string) => {
    const p = new URLSearchParams(parametri);
    p.set(k, v);
    if (!v && k !== "stato") p.delete(k);
    p.delete("pagina");
    setParametri(p);
  };
  if (errore) return <div className="allarme">{errore}</div>;
  if (!r) return <div className="caricamento">Caricamento…</div>;
  const stati = Object.keys(r.stati) as StatoSegnalazione[];

  return (
    <>
      <h1>Segnalazioni</h1>
      <p className="piccolo">Quello che arriva dal pulsante <b>Segnala</b> in basso a destra. I riquadri contano le segnalazioni aperte
        (nuove e prese in carico) per tipo: cliccali per filtrare. Le sessioni di Claude le leggono all'inizio del lavoro e le chiudono
        con una risposta.</p>
      <div className="riquadri">
        {Object.entries(r.tipi).map(([k, t]) => (
          <div key={k} className={"riquadro" + (filtri.tipo === k ? " scelto" : "")} style={{ cursor: "pointer" }}
            onClick={() => { const p = new URLSearchParams(parametri); p.set("tipo", k); p.set("stato", "aperte"); p.delete("pagina"); setParametri(p); }}>
            <div className="etichetta">{t.nome}</div><div className="numero">{r.aperte_per_tipo[k] ?? 0}</div></div>))}
      </div>
      <div className="filtri">
        <select value={filtri.stato} onChange={(e) => imposta("stato", e.target.value)}>
          <option value="aperte">Aperte ({(r.conteggi.nuova ?? 0) + (r.conteggi.presa_in_carico ?? 0)})</option>
          {stati.map((s) => <option key={s} value={s}>{r.stati[s]} ({r.conteggi[s] ?? 0})</option>)}
          <option value="">Tutti gli stati</option>
        </select>
        <select value={filtri.tipo || ""} onChange={(e) => imposta("tipo", e.target.value)}>
          <option value="">Tutti i tipi</option>
          {Object.entries(r.tipi).map(([k, t]) => <option key={k} value={k}>{t.nome}</option>)}
        </select>
        <span className="piccolo">{r.totale} segnalazioni</span>
      </div>
      <table>
        <thead><tr><th>Segnalazione</th><th>Chi e dove</th><th>Stato e risposta</th></tr></thead>
        <tbody>{r.segnalazioni.map((s) => <Riga key={s.id} s={s} tipi={r.tipi} stati={r.stati} ricarica={ricarica} gestisce={gestisce} />)}</tbody>
      </table>
      <div className="pagine">
        <button disabled={r.pagina <= 1} onClick={() => imposta("pagina", String(r.pagina - 1))}>← Precedente</button>
        <span className="piccolo">pagina {r.pagina} di {Math.max(1, Math.ceil(r.totale / r.per_pagina))}</span>
        <button disabled={r.pagina * r.per_pagina >= r.totale} onClick={() => { const p = new URLSearchParams(parametri); p.set("pagina", String(r.pagina + 1)); setParametri(p); }}>Successiva →</button>
      </div>
    </>
  );
}

function Riga({ s, tipi, stati, ricarica, gestisce }: { s: Segnalazione; tipi: Record<string, TipoSegnalazione>;
  stati: Record<StatoSegnalazione, string>; ricarica: () => void; gestisce: boolean }) {
  const [stato, setStato] = useState<StatoSegnalazione>(s.stato);
  const [risposta, setRisposta] = useState(s.risposta || "");
  const [errore, setErrore] = useState<string | null>(null);
  const cambiato = stato !== s.stato || risposta !== (s.risposta || "");
  const salva = async () => {
    try { await api.gestisciSegnalazione(s.id, { stato, risposta }); ricarica(); }
    catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  const campi = tipi[s.tipo]?.campi || {};
  return (
    <tr style={s.stato === "risolta" || s.stato === "respinta" ? { opacity: 0.6 } : undefined}>
      <td><span className="etichetta-tipo">{tipi[s.tipo]?.nome || s.tipo}</span> <span className="piccolo">#{s.id}</span>
        {s.bando_id && <div><Link to={`/bandi/${s.bando_id}`} className="titolo-annuncio">{s.bando_titolo || `Bando ${s.bando_id}`}</Link></div>}
        {Object.entries(s.dettagli || {}).map(([k, v]) => <div key={k}><b>{campi[k] || k}:</b>{" "}
          {/^https?:\/\//.test(v) ? <a href={v} target="_blank" rel="noreferrer">{v}</a> : v}</div>)}
        {s.testo && <div className="testo-lungo" style={{ marginTop: ".3rem" }}>{s.testo}</div>}</td>
      <td>{s.nome || s.email || "utente cancellato"}<div className="piccolo">{s.ruolo || ""} · {data(s.creata_il, true)}</div>
        {s.pagina && <div className="piccolo"><Link to={s.pagina}>{s.pagina}</Link></div>}</td>
      {!gestisce ? <td>{stati[s.stato]}{s.risposta && <div className="piccolo">{s.risposta}</div>}</td> : <td style={{ minWidth: 260 }}>
        <select value={stato} onChange={(e) => setStato(e.target.value as StatoSegnalazione)}>
          {(Object.keys(stati) as StatoSegnalazione[]).map((k) => <option key={k} value={k}>{stati[k]}</option>)}
        </select>
        <textarea rows={2} value={risposta} placeholder="risposta per chi ha scritto" onChange={(e) => setRisposta(e.target.value)} />
        {cambiato && <button onClick={salva}>Salva</button>}
        {s.gestita_da && <div className="piccolo">da {s.gestita_da}{s.gestita_il ? `, ${data(s.gestita_il, true)}` : ""}</div>}
        {errore && <div className="allarme">{errore}</div>}
      </td>}
    </tr>
  );
}
