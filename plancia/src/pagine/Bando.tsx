import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Bando as TipoBando, data, dimensione, NOMI_DECISO_DA, NOMI_RUOLO } from "../api";

// Il bando: per ora la scheda minima senza IA (titolo, ente, indirizzo, chiavi), gli annunci che ne parlano,
// gli allegati e le versioni precedenti. I campi della scheda completa arrivano con Sonnet.
export default function Bando() {
  const { id } = useParams();
  const [b, setB] = useState<TipoBando | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { if (id) api.bando(id).then(setB).catch((e) => setErrore(String(e))); }, [id]);
  if (errore) return <div className="allarme">{errore}</div>;
  if (!b) return <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <p><Link to="/catalogo">← Catalogo</Link></p>
      <h1>{b.titolo}</h1>
      <p className="piccolo">{b.ente} · {b.territorio}{b.codice_ufficiale ? ` · codice ${b.codice_ufficiale}` : ""}
        {b.scadenza ? ` · scade il ${data(b.scadenza)}` : ""} · versione {b.versione}</p>
      {b.url && <p><a href={b.url} target="_blank" rel="noreferrer">Pagina del bando ↗</a></p>}
      {b.sintesi && <p className="testo-lungo">{b.sintesi}</p>}

      <h2>Annunci che parlano di questo bando</h2>
      <table>
        <thead><tr><th>Annuncio</th><th>Ruolo</th><th className="nascondi-mobile">Fonte</th><th className="nascondi-mobile">Trovato</th></tr></thead>
        <tbody>{b.annunci.map((a) => (
          <tr key={a.id}>
            <td><Link to={`/annunci/${a.id}`}>{a.titolo}</Link> <a href={a.url} target="_blank" rel="noreferrer" className="piccolo">originale ↗</a></td>
            <td>{a.ruolo ? NOMI_RUOLO[a.ruolo] : "–"}
              <div className="piccolo">{a.collegato_da ? `da ${NOMI_DECISO_DA[a.collegato_da] || a.collegato_da}` : ""}{a.collegamento_motivo ? `: ${a.collegamento_motivo}` : ""}</div></td>
            <td className="nascondi-mobile piccolo">{a.fonte}</td>
            <td className="nascondi-mobile piccolo">{data(a.pubblicato_il || a.trovato_il)}</td>
          </tr>
        ))}</tbody>
      </table>

      <h2>Allegati del bando</h2>
      {b.allegati.length === 0 ? <p className="piccolo">Nessun allegato ancora.</p> : (
        <table>
          <thead><tr><th>Documento</th><th>Tipo</th><th>Dimensione</th><th className="nascondi-mobile">Note</th></tr></thead>
          <tbody>{b.allegati.map((a) => (
            <tr key={a.id}>
              <td>{a.ha_file ? <a href={`/api/allegati/${a.id}/file`} target="_blank" rel="noreferrer">{a.nome}</a> : a.nome}
                <div className="piccolo"><a href={a.url} target="_blank" rel="noreferrer">originale ↗</a></div></td>
              <td>{a.tipo === "faq" ? "FAQ" : a.tipo === "pagina" ? "pagina web" : a.tipo.toUpperCase()}</td>
              <td>{dimensione(a.dimensione)}</td>
              <td className="nascondi-mobile piccolo">{a.errore ? <span className="errore-allegato">{a.errore}</span>
                : a.caratteri_testo ? `${a.caratteri_testo.toLocaleString("it-IT")} caratteri di testo` : "nessun testo letto"}</td>
            </tr>
          ))}</tbody>
        </table>
      )}

      {b.versioni.length > 0 && (
        <>
          <h2>Versioni precedenti</h2>
          <ul>{b.versioni.map((v) => <li key={v.versione} className="piccolo">versione {v.versione}, fino al {data(v.salvata_il, true)}{v.causa ? ` — ${v.causa}` : ""}</li>)}</ul>
        </>
      )}
    </>
  );
}
