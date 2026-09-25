import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Dubbio } from "../api";

// I doppioni dubbi: la deduplica senza IA non e' sicura che due annunci parlino dello stesso bando.
// Oggi decide Matteo; piu' avanti li smistera' Haiku e qui resteranno solo i casi difficili.
export default function Doppioni() {
  const [pagina, setPagina] = useState(1);
  const [risposta, setRisposta] = useState<{ totale: number; dubbi: Dubbio[] } | null>(null);
  const [decisi, setDecisi] = useState<Record<number, string>>({});
  const carica = () => api.dubbi(pagina).then(setRisposta);
  useEffect(() => { carica(); }, [pagina]);

  const decidi = async (d: Dubbio, decisione: "stesso" | "diverso") => {
    try {
      await api.decidiDubbio(d.id, decisione);
      setDecisi((x) => ({ ...x, [d.id]: decisione === "stesso" ? "unito al bando" : "bando a sé" }));
    } catch (e) {
      alert(String(e));
    }
  };
  const ultima = risposta ? Math.max(1, Math.ceil(risposta.totale / 50)) : 1;
  return (
    <>
      <h1>Doppioni da decidere</h1>
      <div className="avviso">Qui ci sono gli annunci che <b>forse</b> parlano di un bando già noto: titoli simili ma non uguali,
        oppure proroghe e graduatorie di cui non si trova il bando. Finché non decidi restano senza bando.
        <b> Stesso bando</b> li unisce; <b>Bando diverso</b> ne fa un bando a sé.</div>
      {!risposta ? <div className="caricamento">Caricamento…</div> : risposta.totale === 0 ? <p>Nessun dubbio aperto.</p> : (
        <table>
          <thead><tr><th>Annuncio</th><th>Bando candidato</th><th>Decisione</th></tr></thead>
          <tbody>{risposta.dubbi.map((d) => (
            <tr key={d.id}>
              <td><Link to={`/annunci/${d.annuncio_id}`}>{d.titolo}</Link>
                <div className="piccolo">{d.fonte} · <a href={d.url} target="_blank" rel="noreferrer">originale ↗</a></div></td>
              <td>{d.bando_id ? <><Link to={`/bandi/${d.bando_id}`}>{d.bando_titolo}</Link>
                <div className="piccolo">{d.bando_ente} · {d.bando_annunci} annunci{d.bando_url ? <> · <a href={d.bando_url} target="_blank" rel="noreferrer">originale ↗</a></> : null}</div></>
                : <span className="piccolo">nessun bando trovato</span>}
                <div className="piccolo">{d.motivo}</div></td>
              <td className="smistamento">{decisi[d.id] ? <span className="piccolo">✔ {decisi[d.id]}</span> : (
                <div className="correggi">
                  {d.bando_id && <button onClick={() => decidi(d, "stesso")}>Stesso bando</button>}
                  <button onClick={() => decidi(d, "diverso")}>Bando diverso</button>
                </div>)}</td>
            </tr>
          ))}</tbody>
        </table>
      )}
      <div className="pagine">
        <button disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Precedente</button>
        <span className="piccolo">pagina {pagina} di {ultima}{risposta ? ` · ${risposta.totale} dubbi` : ""}</span>
        <button disabled={pagina >= ultima} onClick={() => setPagina(pagina + 1)}>Successiva →</button>
      </div>
    </>
  );
}
