import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Annuncio, api, data, NOMI_TIPO } from "../api";

export default function Catalogo() {
  const [parametri, setParametri] = useSearchParams();
  const [risposta, setRisposta] = useState<{ totale: number; annunci: Annuncio[]; territori: string[] } | null>(null);
  const [testo, setTesto] = useState(parametri.get("q") || "");
  const pagina = Number(parametri.get("pagina") || "1");

  const imposta = (chiave: string, valore: string) => {
    const p = new URLSearchParams(parametri);
    if (valore) p.set(chiave, valore); else p.delete(chiave);
    if (chiave !== "pagina") p.delete("pagina");
    setParametri(p);
  };
  useEffect(() => {
    const p: Record<string, string> = {};
    parametri.forEach((v, k) => (p[k] = v));
    api.annunci(p).then(setRisposta);
  }, [parametri]);

  const perPagina = 50;
  const ultimaPagina = risposta ? Math.max(1, Math.ceil(risposta.totale / perPagina)) : 1;
  return (
    <>
      <h1>Catalogo</h1>
      <div className="avviso">Qui ci sono gli <b>annunci</b> trovati sulle fonti: avvisi, notizie e bandi non ancora smistati. Con la Fase 3 ogni bando avrà la sua scheda e i filtri per ATECO, dimensione e tipo di agevolazione.</div>
      <form className="filtri" onSubmit={(e) => { e.preventDefault(); imposta("q", testo); }}>
        <input type="text" placeholder="Cerca nel titolo, nel riassunto o nell'ente…" value={testo} onChange={(e) => setTesto(e.target.value)} />
        <button type="submit">Cerca</button>
        <select value={parametri.get("tipo") || ""} onChange={(e) => imposta("tipo", e.target.value)}>
          <option value="">Tutti i tipi di fonte</option>
          {Object.entries(NOMI_TIPO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={parametri.get("territorio") || ""} onChange={(e) => imposta("territorio", e.target.value)}>
          <option value="">Tutti i territori</option>
          {risposta?.territori.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <label className="piccolo">dal <input type="date" value={parametri.get("da") || ""} onChange={(e) => imposta("da", e.target.value)} /></label>
        <label className="piccolo">al <input type="date" value={parametri.get("a") || ""} onChange={(e) => imposta("a", e.target.value)} /></label>
        <select value={parametri.get("scadenza_entro") || ""} onChange={(e) => imposta("scadenza_entro", e.target.value)}>
          <option value="">Qualunque scadenza</option>
          <option value="7">Scade entro 7 giorni</option><option value="30">Scade entro 30 giorni</option><option value="90">Scade entro 90 giorni</option>
        </select>
        {risposta && <span className="piccolo">{risposta.totale} annunci</span>}
      </form>
      {!risposta ? <div className="caricamento">Caricamento…</div> : (
        <table>
          <thead><tr><th>Data</th><th>Annuncio</th><th>Scadenza</th><th className="nascondi-mobile">Fonte</th></tr></thead>
          <tbody>{risposta.annunci.map((a) => (
            <tr key={a.id}>
              <td>{data(a.pubblicato_il || a.trovato_il)}</td>
              <td><a href={a.url} target="_blank" rel="noreferrer" className="titolo-annuncio">{a.titolo}</a>
                {a.riassunto && <div className="riassunto">{a.riassunto.slice(0, 220)}</div>}</td>
              <td className="scadenza">{a.scadenza ? data(a.scadenza) : ""}</td>
              <td className="nascondi-mobile"><span className="etichetta-tipo">{NOMI_TIPO[a.tipo] || a.tipo}</span>{a.ente}<div className="piccolo">{a.territorio}</div></td>
            </tr>
          ))}</tbody>
        </table>
      )}
      <div className="pagine">
        <button disabled={pagina <= 1} onClick={() => imposta("pagina", String(pagina - 1))}>← Precedente</button>
        <span className="piccolo">pagina {pagina} di {ultimaPagina}</span>
        <button disabled={pagina >= ultimaPagina} onClick={() => imposta("pagina", String(pagina + 1))}>Successiva →</button>
      </div>
    </>
  );
}
