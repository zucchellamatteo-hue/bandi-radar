import { useEffect, useState } from "react";
import { api, data, Visite as DatiVisite } from "../api";

// Visite (08/10/2026, richiesta di Matteo): quante persone e quanti programmi (motori di ricerca, IA) leggono le pagine
// pubbliche (/, /blog, articoli, /llms.txt, sitemap, robots). Solo contatori anonimi per giorno, senza cookie: niente
// IP, niente identificativi (app/visite). Serve a vedere ogni due settimane se SEO e GEO funzionano (PIANO_SEO_GEO.md).
const GRUPPI: Record<string, string> = {
  ia: "motore IA", motore: "motore di ricerca", social: "social", diretto: "diretto", interno: "dal nostro sito", altro: "altro sito",
};
const n = (x: number) => x.toLocaleString("it-IT");

export default function Visite() {
  const [giorni, setGiorni] = useState(30);
  const [d, setD] = useState<DatiVisite | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { setD(null); api.visite(giorni).then(setD).catch((e) => setErrore(String(e.message || e))); }, [giorni]);
  if (errore) return <div className="allarme">{errore}</div>;
  if (!d) return <div className="caricamento">Caricamento…</div>;
  const t = d.totali;
  const ia = d.programmi.filter((p) => p.visitatore === "ia");
  const motori = d.programmi.filter((p) => p.visitatore === "motore");
  return (
    <>
      <h1>Visite</h1>
      <div className="avviso">Chi legge le pagine pubbliche: la presentazione (/), il blog e i suoi articoli, /llms.txt, la
        mappa del sito e robots.txt. Sono <b>solo conteggi anonimi per giorno</b>, senza cookie e senza indirizzi IP: non
        sappiamo chi è passato, solo quante volte, da dove (Google, ChatGPT…) e se era una persona o un programma. Le
        visite di chi ha fatto l'accesso (noi) non si contano.{" "}
        <label>Periodo: <select value={giorni} onChange={(e) => setGiorni(Number(e.target.value))}>
          <option value={7}>ultimi 7 giorni</option><option value={30}>ultimi 30 giorni</option>
          <option value={90}>ultimi 90 giorni</option><option value={365}>ultimo anno</option></select></label></div>
      <div className="riquadri">
        <div className="riquadro"><div className="numero">{n(t.persone)}</div><div className="etichetta">visite di persone</div></div>
        <div className="riquadro"><div className="numero">{n(t.persone_da_ia)}</div><div className="etichetta">persone arrivate da un motore IA</div>
          <div className="piccolo">ChatGPT, Perplexity, Gemini, Copilot, Claude…</div></div>
        <div className="riquadro"><div className="numero">{n(t.ia)}</div><div className="etichetta">letture dei programmi IA</div>
          <div className="piccolo">GPTBot, ClaudeBot, PerplexityBot…</div></div>
        <div className="riquadro"><div className="numero">{n(t.motori)}</div><div className="etichetta">letture dei motori di ricerca</div>
          <div className="piccolo">Googlebot, Bingbot…</div></div>
      </div>

      <h2>Visite per giorno</h2>
      {!d.per_giorno.length ? <p>Nessuna visita nel periodo.</p> : <table>
        <thead><tr><th>Giorno</th><th>Persone</th><th>Motori di ricerca</th><th>Programmi IA</th><th className="nascondi-mobile">Altri programmi</th></tr></thead>
        <tbody>{d.per_giorno.map((g) => <tr key={g.giorno}><td>{data(g.giorno)}</td><td><b>{n(g.persone)}</b></td>
          <td>{n(g.motori)}</td><td>{n(g.ia)}</td><td className="nascondi-mobile">{n(g.altri)}</td></tr>)}</tbody></table>}

      <h2>Pagine più viste</h2>
      {!d.pagine.length ? <p>Nessuna pagina vista nel periodo.</p> : <table>
        <thead><tr><th>Pagina</th><th>Persone</th><th>Motori di ricerca</th><th>Programmi IA</th><th className="nascondi-mobile">Altri programmi</th></tr></thead>
        <tbody>{d.pagine.map((p) => <tr key={p.percorso}><td><a href={p.percorso} target="_blank" rel="noopener">{p.percorso}</a></td>
          <td><b>{n(p.persone)}</b></td><td>{n(p.motori)}</td><td>{n(p.ia)}</td><td className="nascondi-mobile">{n(p.altri)}</td></tr>)}</tbody></table>}

      <h2>Da dove arrivano le persone</h2>
      <p className="piccolo">Solo il sito di provenienza (per esempio google.it o chatgpt.com), mai l'indirizzo completo.
        "Diretto" = link scritto a mano, segnalibro, email o app che non dice da dove arrivi. In evidenza i motori IA.</p>
      {!d.provenienze.length ? <p>Nessuna visita nel periodo.</p> : <table>
        <thead><tr><th>Provenienza</th><th>Tipo</th><th>Visite</th></tr></thead>
        <tbody>{d.provenienze.map((p) => <tr key={p.provenienza} className={p.gruppo === "ia" ? "filtro-attivo" : ""}>
          <td>{p.gruppo === "ia" ? <b>{p.provenienza}</b> : p.provenienza}</td>
          <td>{p.gruppo === "ia" ? <span className="etichetta-tipo"><b>{GRUPPI.ia}</b></span> : GRUPPI[p.gruppo] || p.gruppo}</td>
          <td>{n(p.visite)}</td></tr>)}</tbody></table>}

      <Programmi titolo="Programmi delle IA, pagina per pagina" righe={ia}
        spiegazione="Le letture dei programmi di OpenAI, Anthropic, Perplexity, Google (Gemini), Meta, Apple...: chi raccoglie testi per le risposte o per l'addestramento. Se leggono gli articoli, possono citarci." />
      <Programmi titolo="Motori di ricerca, pagina per pagina" righe={motori}
        spiegazione="Googlebot, Bingbot e gli altri: se passano su un articolo, quell'articolo può entrare nei risultati di ricerca." />

      <h2>Campagne (parametri utm)</h2>
      <p className="piccolo">Le visite arrivate da link con utm_source, utm_medium o utm_campaign (annunci, newsletter, post su
        LinkedIn). ChatGPT aggiunge da solo utm_source=chatgpt.com ai link che mostra.</p>
      {!d.campagne.length ? <p>Nessuna visita da link con parametri utm nel periodo.</p> : <table>
        <thead><tr><th>utm_source</th><th>utm_medium</th><th>utm_campaign</th><th>Visite</th></tr></thead>
        <tbody>{d.campagne.map((c, i) => <tr key={i}><td>{c.utm_source || "–"}</td><td>{c.utm_medium || "–"}</td>
          <td>{c.utm_campaign || "–"}</td><td>{n(c.visite)}</td></tr>)}</tbody></table>}
    </>
  );
}

function Programmi({ titolo, righe, spiegazione }: { titolo: string; righe: DatiVisite["programmi"]; spiegazione: string }) {
  return (
    <>
      <h2>{titolo}</h2>
      <p className="piccolo">{spiegazione}</p>
      {!righe.length ? <p>Nessuna lettura nel periodo.</p> : <table>
        <thead><tr><th>Pagina</th><th>Programma</th><th>Letture</th><th className="nascondi-mobile">Ultima</th></tr></thead>
        <tbody>{righe.map((p) => <tr key={`${p.percorso}|${p.programma}`}><td>{p.percorso}</td><td>{p.programma}</td>
          <td>{n(p.visite)}</td><td className="nascondi-mobile">{data(p.ultima)}</td></tr>)}</tbody></table>}
    </>
  );
}
