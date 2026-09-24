import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, data, NOMI_TIPO, SettimanaDettaglio } from "../api";

const MASSIMO = 40;

export default function Settimana() {
  const { chiave } = useParams();
  const [dati, setDati] = useState<SettimanaDettaglio | null>(null);
  const [aperti, setAperti] = useState<Record<string, boolean>>({});
  useEffect(() => { if (chiave) api.settimana(chiave).then(setDati); }, [chiave]);
  if (!dati) return <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <p><Link to="/novita">← Tutte le settimane</Link></p>
      <h1>Novità dal {data(dati.inizio)} al {data(dati.fine)}</h1>
      <p className="piccolo">{dati.totale} elementi nuovi trovati sulle fonti, raggruppati per tipo di ente. Non sono ancora smistati: gare e concorsi compaiono insieme ai bandi.</p>
      {dati.gruppi.map((g) => {
        const tutti = aperti[g.tipo];
        const voci = tutti ? g.annunci : g.annunci.slice(0, MASSIMO);
        return (
          <section key={g.tipo}>
            <h2>{NOMI_TIPO[g.tipo] || g.tipo} <span className="piccolo">({g.annunci.length})</span></h2>
            <table><tbody>{voci.map((a) => (
              <tr key={a.id}>
                <td style={{ width: 90 }}>{data(a.pubblicato_il || a.trovato_il)}</td>
                <td><a href={a.url} target="_blank" rel="noreferrer" className="titolo-annuncio">{a.titolo}</a><div className="piccolo">{a.ente}{a.scadenza ? <span className="scadenza"> · scade il {data(a.scadenza)}</span> : null}</div></td>
              </tr>
            ))}</tbody></table>
            {g.annunci.length > MASSIMO && !tutti && (
              <p><button onClick={() => setAperti({ ...aperti, [g.tipo]: true })}>Mostra tutti i {g.annunci.length}</button></p>
            )}
          </section>
        );
      })}
    </>
  );
}
