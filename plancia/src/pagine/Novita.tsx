import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, data, Settimana } from "../api";

export default function Novita() {
  const [settimane, setSettimane] = useState<Settimana[] | null>(null);
  useEffect(() => { api.settimane().then(setSettimane); }, []);
  if (!settimane) return <div className="caricamento">Caricamento…</div>;
  return (
    <>
      <h1>Novità della settimana</h1>
      <p className="piccolo">Una voce per settimana: le stesse novità che arrivano il lunedì per email.</p>
      <ul className="lista-settimane">
        {settimane.map((s) => (
          <li key={s.chiave}>
            <span><Link to={`/novita/${s.chiave}`}><b>Settimana dal {data(s.inizio)}</b></Link> <span className="piccolo">({s.chiave})</span></span>
            <span className="piccolo">{s.n} novità da {s.fonti} fonti</span>
          </li>
        ))}
      </ul>
    </>
  );
}
