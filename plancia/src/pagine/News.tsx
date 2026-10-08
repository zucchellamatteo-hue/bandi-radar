import { useEffect, useState } from "react";
import { api, data, News as Notizia } from "../api";
import { usePuo } from "../utente";

// News (07/10/2026, richiesta di Matteo): brevi notizie per chi segue i bandi. Nascono in bozza; quando sono pubblicate
// e oggi e' nel loro periodo entrano nell'email del lunedi' alle imprese (una volta sola per impresa) e in cima alla Guida.
const oggi = () => new Date().toISOString().slice(0, 10);
const VUOTA = { titolo: "", testo: "", link: "", da: oggi(), a: "", pubblico: "imprese" };

function situazione(n: Notizia): string {
  if (n.stato === "bozza") return "bozza";
  if (n.da > oggi()) return `pubblicata, parte dal ${data(n.da)}`;
  if (n.a && n.a < oggi()) return "pubblicata, periodo finito";
  return "pubblicata, attiva ora";
}

export default function News() {
  const modifiche = usePuo("modifiche");
  const [r, setR] = useState<Awaited<ReturnType<typeof api.news>> | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [nuova, setNuova] = useState(VUOTA);
  const ricarica = () => api.news().then(setR).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { ricarica(); }, []);
  const azione = async (f: () => Promise<unknown>) => {
    setErrore(null);
    try { await f(); ricarica(); return true; } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); return false; }
  };
  if (!r) return errore ? <div className="allarme">{errore}</div> : <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <h1>News</h1>
      <p className="piccolo">Poche righe sulle novità di bandinQiaro o su notizie utili a chi segue i bandi. Una news nasce
        in <b>bozza</b>: quando la <b>pubblichi</b>, nel periodo scelto entra nell'email del lunedì alle imprese (una volta
        sola per impresa) e compare in cima alla loro Guida. Pubblico "imprese e collaboratori": la vedono anche revisori e staff.</p>
      {modifiche && <form className="riquadro" onSubmit={async (e) => {
        e.preventDefault();
        if (await azione(() => api.creaNews({ ...nuova, link: nuova.link || null, a: nuova.a || null }))) setNuova(VUOTA);
      }}>
        <h2>Nuova news</h2>
        <Campi n={nuova} pubblici={r.pubblici} cambia={(c) => setNuova({ ...nuova, ...c })} />
        <button type="submit" className="primario">Salva come bozza</button>
      </form>}
      {errore && <div className="allarme">{errore}</div>}
      {!r.news.length && <p>Nessuna news.</p>}
      {r.news.map((n) => <Voce key={n.id} n={n} modifiche={modifiche} pubblici={r.pubblici} azione={azione} />)}
    </>
  );
}

type Modulo = { titolo: string; testo: string; link: string; da: string; a: string; pubblico: string };

function Campi({ n, pubblici, cambia }: { n: Modulo; pubblici: Record<string, string>; cambia: (c: Partial<Modulo>) => void }) {
  return (
    <div className="modulo-news">
      <input type="text" placeholder="titolo" value={n.titolo} maxLength={200} required style={{ width: "100%" }}
        onChange={(e) => cambia({ titolo: e.target.value })} />
      <textarea rows={4} placeholder="testo: poche righe, semplici" value={n.testo} maxLength={1200} required
        style={{ width: "100%" }} onChange={(e) => cambia({ testo: e.target.value })} />
      <div className="filtri">
        <input type="text" placeholder="link facoltativo (https://... oppure /impresa/misure)" value={n.link}
          style={{ minWidth: 280 }} onChange={(e) => cambia({ link: e.target.value })} />
        <label className="piccolo">dal <input type="date" value={n.da} required onChange={(e) => cambia({ da: e.target.value })} /></label>
        <label className="piccolo">al <input type="date" value={n.a} onChange={(e) => cambia({ a: e.target.value })} /></label>
        <select value={n.pubblico} onChange={(e) => cambia({ pubblico: e.target.value })}>
          {Object.entries(pubblici).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
      </div>
      <p className="piccolo">{n.testo.length}/1200 caratteri · "al" vuoto = finché non la togli</p>
    </div>
  );
}

function Voce({ n, modifiche, pubblici, azione }: { n: Notizia; modifiche: boolean; pubblici: Record<string, string>;
  azione: (f: () => Promise<unknown>) => Promise<boolean> }) {
  const [modulo, setModulo] = useState<Modulo | null>(null);
  if (modulo) return (
    <form className="riquadro" onSubmit={async (e) => {
      e.preventDefault();
      if (await azione(() => api.modificaNews(n.id, { ...modulo, link: modulo.link || null, a: modulo.a || null }))) setModulo(null);
    }}>
      <Campi n={modulo} pubblici={pubblici} cambia={(c) => setModulo({ ...modulo, ...c })} />
      <button type="submit" className="primario">Salva</button>{" "}
      <button type="button" onClick={() => setModulo(null)}>Annulla</button>
    </form>
  );
  return (
    <div className="riquadro" style={n.stato === "bozza" ? { borderStyle: "dashed" } : undefined}>
      <div><b>{n.titolo}</b> <span className="piccolo">· {situazione(n)}</span></div>
      <p className="testo-lungo">{n.testo}</p>
      {n.link && <p className="piccolo">Link: {n.link}</p>}
      <p className="piccolo">#{n.id} · dal {data(n.da)}{n.a ? ` al ${data(n.a)}` : ""} · {pubblici[n.pubblico] || n.pubblico}
        {n.creata_da ? ` · scritta da ${n.creata_da}` : ""}{n.aggiornata_da && n.aggiornata_da !== n.creata_da ? `, modificata da ${n.aggiornata_da}` : ""}</p>
      {modifiche && <div>
        {n.stato === "bozza"
          ? <button className="primario" onClick={() => azione(() => api.modificaNews(n.id, { stato: "pubblicata" }))}>Pubblica</button>
          : <button onClick={() => azione(() => api.modificaNews(n.id, { stato: "bozza" }))}>Rimetti in bozza</button>}{" "}
        <button onClick={() => setModulo({ titolo: n.titolo, testo: n.testo, link: n.link || "", da: n.da.slice(0, 10),
          a: n.a ? n.a.slice(0, 10) : "", pubblico: n.pubblico })}>Modifica</button>{" "}
        <button onClick={() => { if (confirm("Cancellare questa news?")) azione(() => api.cancellaNews(n.id)); }}>✗</button>
      </div>}
    </div>
  );
}
