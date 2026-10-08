import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, data, euro } from "../api";

// Campagne di lancio (05/10/2026): profili anonimi delle imprese di Matteo abbinati ai bandi recenti, con la bozza del
// testo da completare sul suo computer. Niente nomi in bandinQiaro.
export default function Campagne() {
  const { id } = useParams();
  return id ? <Dettaglio id={Number(id)} /> : <Elenco />;
}

function Avvertenza() {
  return (
    <div className="allarme"><b>Prima di contattare le imprese.</b> In Italia le email promozionali non richieste sono vietate anche verso
      le società (art. 130 Codice privacy; il Garante ha sanzionato anche indirizzi presi dal web e PEC). Usa questi testi per lettere
      cartacee alle società, o per email solo a chi ti ha dato il consenso, dopo il via libera di un avvocato. Dettagli in
      docs/ricerche/2026-10-05_marketing_prospect_regole.md.</div>
  );
}

function Elenco() {
  const [campagne, setCampagne] = useState<Awaited<ReturnType<typeof api.campagne>>>([]);
  const [nome, setNome] = useState("Prima campagna");
  const [giorni, setGiorni] = useState(60);
  const [file, setFile] = useState<File | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [inCorso, setInCorso] = useState(false);
  const ricarica = () => api.campagne().then(setCampagne).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); const t = setInterval(ricarica, 10000); return () => clearInterval(t); }, []);
  const carica = async (e: React.FormEvent) => {
    e.preventDefault(); setErrore(null);
    if (!file) { setErrore("Scegli il file profili_anonimi.json."); return; }
    setInCorso(true);
    try {
      const contenuto = JSON.parse(await file.text());
      await api.creaCampagna({ nome, giorni, profili: contenuto.profili || contenuto });
      ricarica();
    } catch (err) { setErrore(err instanceof Error ? err.message : String(err)); }
    setInCorso(false);
  };
  return (
    <>
      <h1>Campagne</h1>
      <Avvertenza />
      <p>Come si fa: 1) sul tuo computer lanci <code>strumenti/anagrafiche/esporta_profili.py</code>, che legge il database delle
        anagrafiche e prepara <code>profili_anonimi.json</code> (solo codici e dati di categoria, niente nomi); 2) lo carichi qui;
        3) bandinQiaro trova per ogni impresa i bandi compatibili usciti negli ultimi giorni e prepara la bozza del testo; 4) scarichi il
        CSV e lo unisci a casa con <code>corrispondenze.csv</code> (codice → impresa).</p>
      <form className="filtri" onSubmit={carica}>
        <input type="text" value={nome} onChange={(e) => setNome(e.target.value)} placeholder="nome della campagna" />
        <label>bandi degli ultimi <input type="number" min={7} max={365} value={giorni} style={{ width: 70 }}
          onChange={(e) => setGiorni(Number(e.target.value))} /> giorni</label>
        <input type="file" accept=".json,application/json" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button type="submit" disabled={inCorso}>{inCorso ? "Carico…" : "Carica e analizza"}</button>
      </form>
      {errore && <div className="allarme">{errore}</div>}
      <table>
        <thead><tr><th>Campagna</th><th>Imprese</th><th>Con bandi compatibili</th><th>Stato</th><th>Creata</th></tr></thead>
        <tbody>{campagne.map((c) => (
          <tr key={c.id}><td><Link to={`/campagne/${c.id}`}>{c.nome}</Link><div className="piccolo">bandi degli ultimi {c.giorni} giorni</div></td>
            <td>{c.prospetti}</td><td>{c.riepilogo?.con_compatibili ?? "–"}</td>
            <td>{c.stato === "in_analisi" ? "in analisi…" : c.stato}{c.riepilogo?.errore ? `: ${c.riepilogo.errore}` : ""}</td>
            <td>{data(c.creata_il, true)}</td></tr>))}</tbody>
      </table>
    </>
  );
}

const NOMI_DIMENSIONE: Record<string, string> = { micro: "micro", piccola: "piccola", media: "media", grande: "grande" };

function Dettaglio({ id }: { id: number }) {
  const [c, setC] = useState<Awaited<ReturnType<typeof api.campagna>> | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => {
    const leggi = () => api.campagna(id).then(setC).catch((e) => setErrore(String(e.message || e)));
    leggi(); const t = setInterval(() => { if (c?.stato !== "pronta") leggi(); }, 8000); return () => clearInterval(t);
  }, [id, c?.stato]);
  if (errore) return <div className="allarme">{errore}</div>;
  if (!c) return <div className="caricamento">Caricamento…</div>;
  const r = c.riepilogo || {};
  return (
    <>
      <p><Link to="/campagne">← Campagne</Link></p>
      <h1>{c.nome}</h1>
      {c.stato !== "pronta" ? <div className="avviso">{c.stato === "errore" ? `Errore: ${r.errore}` : "Analisi in corso: la pagina si aggiorna da sola."}</div> : (
        <>
          <div className="riquadri">
            <div className="riquadro"><div className="etichetta">Imprese caricate</div><div className="numero">{r.prospetti}</div></div>
            <div className="riquadro"><div className="etichetta">Con bandi compatibili</div><div className="numero">{r.con_compatibili}</div></div>
            <div className="riquadro"><div className="etichetta">Bandi considerati</div><div className="numero">{r.bandi_considerati}</div>
              <div className="piccolo">aperti o in arrivo, scheda degli ultimi {c.giorni} giorni</div></div>
          </div>
          <p><a href={`/api/campagne/${id}/esporta`}><button className="primario">Scarica il CSV con le bozze</button></a>{" "}
            <span className="piccolo">Una riga per impresa con almeno un bando compatibile: codice, bandi, beneficio massimo, oggetto e testo
            con {"{RAGIONE_SOCIALE}"} e {"{FIRMA}"} da sostituire.</span></p>
          <Avvertenza />
          <h2>I bandi che interessano più imprese</h2>
          <table><tbody>{(r.bandi_piu_utili || []).map((b: { bando_id: number; titolo: string; imprese: number }) => (
            <tr key={b.bando_id}><td><Link to={`/bandi/${b.bando_id}`}>{b.titolo}</Link></td><td>{b.imprese} imprese</td></tr>))}</tbody></table>
          <h2>Dove la proposta è più forte</h2>
          <p className="piccolo">Imprese per settore (prime due cifre ATECO), regione e dimensione stimata.</p>
          <table>
            <thead><tr><th>ATECO</th><th>Regione</th><th>Dimensione</th><th>Imprese</th><th>Con bandi</th><th>Bandi in media</th><th>Beneficio mediano</th></tr></thead>
            <tbody>{c.segmenti.slice(0, 60).map((s, i) => (
              <tr key={i}><td>{s.ateco}</td><td>{s.regione}</td><td>{NOMI_DIMENSIONE[s.dimensione] || s.dimensione}</td><td>{s.imprese}</td>
                <td>{s.con_compatibili}</td><td>{s.media_bandi}</td><td>{s.beneficio_mediano ? `fino a ${euro(s.beneficio_mediano)}` : "–"}</td></tr>))}</tbody>
          </table>
          {c.esempio && <><h2>Esempio di testo ({c.esempio.codice})</h2><p><b>{c.esempio.oggetto}</b></p>
            <pre className="testo-lungo">{c.esempio.testo}</pre></>}
        </>
      )}
    </>
  );
}
