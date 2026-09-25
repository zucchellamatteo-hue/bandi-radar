import { useState } from "react";
import { Link } from "react-router-dom";
import { AnnuncioDelBando, api, BandoBreve, data, DubbioAnnuncio, NOMI_DECISO_DA, NOMI_RUOLO, Ruolo } from "./api";

// Nella pagina dell'annuncio: il bando a cui e' collegato, gli altri annunci dello stesso bando,
// i dubbi aperti e i comandi per unire o separare a mano.
export default function BandoCollegato({ annuncioId, bando, ruolo, collegatoDa, motivo, altri, dubbi, aggiorna }: {
  annuncioId: number; bando: BandoBreve | null; ruolo: Ruolo | null; collegatoDa: string | null; motivo: string | null;
  altri: AnnuncioDelBando[]; dubbi: DubbioAnnuncio[]; aggiorna: () => void;
}) {
  const [conAnnuncio, setConAnnuncio] = useState("");
  const [inCorso, setInCorso] = useState(false);
  const esegui = async (corpo: Parameters<typeof api.cambiaBando>[1]) => {
    setInCorso(true);
    try {
      await api.cambiaBando(annuncioId, corpo);
      setConAnnuncio("");
      aggiorna();
    } catch (e) {
      alert(String(e));
    } finally {
      setInCorso(false);
    }
  };
  return (
    <>
      <h2>Bando</h2>
      {bando ? (
        <p>
          <Link to={`/bandi/${bando.id}`} className="titolo-annuncio">{bando.titolo}</Link>
          <span className="piccolo"> · {bando.ente}{bando.codice_ufficiale ? ` · codice ${bando.codice_ufficiale}` : ""}
            {bando.scadenza ? ` · scade il ${data(bando.scadenza)}` : ""}</span>
          <br /><span className="piccolo">Questo annuncio è: <b>{ruolo ? NOMI_RUOLO[ruolo] : "–"}</b>
            {collegatoDa ? ` (collegato da ${NOMI_DECISO_DA[collegatoDa] || collegatoDa}${motivo ? `: ${motivo}` : ""})` : ""}</span>
        </p>
      ) : (
        <p className="piccolo">Non ancora collegato a un bando. Si collegano gli annunci rilevanti con <code>python -m app.schede.bandi</code>.</p>
      )}
      {dubbi.length > 0 && (
        <div className="avviso">
          <b>Doppione dubbio.</b> {dubbi.map((d) => (
            <div key={d.id}>
              {d.bando_id ? <>Forse è lo stesso bando di <Link to={`/bandi/${d.bando_id}`}>{d.bando_titolo}</Link></> : "È un aggiornamento, ma non trovo il bando"}
              {" "}<span className="piccolo">({d.motivo})</span>{" "}
              <Link to="/doppioni">decidi nella pagina Doppioni</Link>
            </div>
          ))}
        </div>
      )}
      {altri.length > 0 && (
        <>
          <h2>Altri annunci dello stesso bando</h2>
          <table>
            <thead><tr><th>Annuncio</th><th>Ruolo</th><th className="nascondi-mobile">Fonte</th></tr></thead>
            <tbody>{altri.map((a) => (
              <tr key={a.id}>
                <td><Link to={`/annunci/${a.id}`}>{a.titolo}</Link> <a href={a.url} target="_blank" rel="noreferrer" className="piccolo">originale ↗</a></td>
                <td>{a.ruolo ? NOMI_RUOLO[a.ruolo] : "–"}<div className="piccolo">{a.collegamento_motivo}</div></td>
                <td className="nascondi-mobile piccolo">{a.fonte}</td>
              </tr>
            ))}</tbody>
          </table>
        </>
      )}
      <div className="filtri" style={{ marginTop: ".8rem" }}>
        <form onSubmit={(e) => { e.preventDefault(); if (conAnnuncio) esegui({ azione: "unisci", con_annuncio: Number(conAnnuncio) }); }}>
          <input type="number" min={1} placeholder="n. di un altro annuncio" value={conAnnuncio} onChange={(e) => setConAnnuncio(e.target.value)} />
          {" "}<button type="submit" disabled={inCorso || !conAnnuncio} title="Questo annuncio parla dello stesso bando dell'annuncio indicato">Unisci allo stesso bando</button>
        </form>
        {bando && (altri.length > 0 || dubbi.length > 0) && (
          <button disabled={inCorso} onClick={() => esegui({ azione: "separa" })} title="Questo annuncio parla di un bando diverso">
            Separa: è un bando a sé</button>
        )}
      </div>
      <p className="piccolo">Il numero dell'annuncio è nell'indirizzo della sua pagina (…/annunci/<b>123</b>). Le tue scelte non vengono mai cambiate dalla deduplica automatica.</p>
    </>
  );
}
