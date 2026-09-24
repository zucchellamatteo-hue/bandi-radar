import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Annuncio, api, Controllo, data, Fonte } from "../api";

export default function DettaglioFonte() {
  const { id } = useParams();
  const [dati, setDati] = useState<{ fonte: Fonte; controlli: Controllo[]; annunci: Annuncio[] } | null>(null);
  useEffect(() => { if (id) api.fonte(id).then(setDati); }, [id]);
  if (!dati) return <div className="caricamento">Caricamento…</div>;
  const f = dati.fonte;
  return (
    <>
      <p><Link to="/">← Fonti</Link></p>
      <h1>{f.nome}</h1>
      <p className="piccolo">{f.ente} · {f.tipo} · {f.territorio} · modalità {f.modalita} · frequenza {f.frequenza.replace(/_/g, " ")} · stato nel registro: {f.stato}{f.in_pausa ? " · IN PAUSA" : ""}</p>
      {f.url && <p><a href={f.url} target="_blank" rel="noreferrer">{f.url}</a></p>}
      <h2>Ultimi controlli</h2>
      <table>
        <thead><tr><th>Quando</th><th>Esito</th><th>HTTP</th><th>Durata</th><th>Elementi</th><th>Novità</th><th>Messaggio</th></tr></thead>
        <tbody>{dati.controlli.map((c) => (
          <tr key={c.id}><td>{data(c.iniziato_il, true)}</td><td>{c.esito}</td><td>{c.codice_http ?? "–"}</td>
            <td>{c.durata_ms != null ? `${(c.durata_ms / 1000).toFixed(1)} s` : "–"}</td><td>{c.elementi_letti}</td><td>{c.novita}</td>
            <td className="piccolo">{c.messaggio}</td></tr>
        ))}</tbody>
      </table>
      <h2>Ultimi annunci trovati</h2>
      <table>
        <thead><tr><th>Data</th><th>Titolo</th><th>Trovato il</th></tr></thead>
        <tbody>{dati.annunci.map((a) => (
          <tr key={a.id}><td>{data(a.pubblicato_il)}</td>
            <td><a href={a.url} target="_blank" rel="noreferrer" className="titolo-annuncio">{a.titolo}</a>{a.riassunto && <div className="riassunto">{a.riassunto.slice(0, 200)}</div>}</td>
            <td>{data(a.trovato_il)}</td></tr>
        ))}</tbody>
      </table>
    </>
  );
}
