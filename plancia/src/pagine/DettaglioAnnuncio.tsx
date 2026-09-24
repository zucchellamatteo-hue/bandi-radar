import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Allegato, api, data, dimensione, NOMI_DECISO_DA, NOMI_ESITO, NOMI_TIPO, Smistamento as RigaSmistamento } from "../api";
import Smistamento from "../Smistamento";

type Dettaglio = Awaited<ReturnType<typeof api.annuncio>>;

export default function DettaglioAnnuncio() {
  const { id } = useParams();
  const [dati, setDati] = useState<Dettaglio | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  useEffect(() => { if (id) api.annuncio(id).then(setDati).catch((e) => setErrore(String(e))); }, [id]);
  if (errore) return <div className="allarme">{errore}</div>;
  if (!dati) return <div className="caricamento">Caricamento…</div>;
  const s: RigaSmistamento | null = dati.smistamento;
  const scaricati = dati.allegati.filter((a) => a.ha_file);
  const mancati = dati.allegati.filter((a) => !a.ha_file);
  return (
    <>
      <p><Link to="/catalogo">← Catalogo</Link></p>
      <h1>{dati.titolo}</h1>
      <p className="piccolo">
        <span className="etichetta-tipo">{NOMI_TIPO[dati.tipo] || dati.tipo}</span>
        {dati.ente} · {dati.territorio} · fonte <Link to={`/fonti/${dati.fonte_id}`}>{dati.fonte}</Link>
        {" "}· pubblicato {data(dati.pubblicato_il)} · trovato {data(dati.trovato_il)}
      </p>
      <p><a href={dati.url} target="_blank" rel="noreferrer">Pagina originale dell'ente ↗</a></p>
      {dati.riassunto && <p className="testo-lungo">{dati.riassunto}</p>}

      <h2>Smistamento</h2>
      <Smistamento annuncioId={dati.id} esito={s?.esito} decisoDa={s?.deciso_da} motivo={s?.motivo} />
      {s?.motivo && <p className="piccolo">Motivo: {s.motivo}</p>}
      {s?.proposta_esito && (
        <p className="piccolo">Proposta originale ({NOMI_DECISO_DA[s.proposta_da || ""] || s.proposta_da}): {NOMI_ESITO[s.proposta_esito]}
          {s.proposta_motivo ? ` — ${s.proposta_motivo}` : ""}</p>
      )}

      <h2>Allegati scaricati</h2>
      {dati.allegati.length === 0 ? (
        <p className="piccolo">Nessun allegato ancora. Si scaricano per gli annunci rilevanti con <code>python -m app.schede.allegati</code>.</p>
      ) : (
        <TabellaAllegati allegati={scaricati} />
      )}
      {mancati.length > 0 && (
        <>
          <h2>Documenti trovati ma non scaricati</h2>
          <table>
            <thead><tr><th>Documento</th><th>Tipo</th><th>Motivo</th></tr></thead>
            <tbody>{mancati.map((a) => (
              <tr key={a.id}><td><a href={a.url} target="_blank" rel="noreferrer">{a.nome}</a></td><td>{a.tipo}</td>
                <td className="errore-allegato">{a.errore}</td></tr>
            ))}</tbody>
          </table>
        </>
      )}
    </>
  );
}

function TabellaAllegati({ allegati }: { allegati: Allegato[] }) {
  if (allegati.length === 0) return <p className="piccolo">Nessun file scaricato.</p>;
  return (
    <table>
      <thead><tr><th>Documento</th><th>Tipo</th><th>Dimensione</th><th>Scaricato il</th><th className="nascondi-mobile">Testo letto</th></tr></thead>
      <tbody>{allegati.map((a) => (
        <tr key={a.id}>
          <td><a href={`/api/allegati/${a.id}/file`} target="_blank" rel="noreferrer">{a.nome}</a>
            <div className="piccolo"><a href={a.url} target="_blank" rel="noreferrer">originale ↗</a></div></td>
          <td>{a.tipo === "faq" ? "FAQ" : a.tipo.toUpperCase()}</td>
          <td>{dimensione(a.dimensione)}</td>
          <td>{data(a.scaricato_il, true)}</td>
          <td className="nascondi-mobile piccolo">{a.caratteri_testo ? `${a.caratteri_testo.toLocaleString("it-IT")} caratteri` : "nessun testo (scansione o formato non letto)"}</td>
        </tr>
      ))}</tbody>
    </table>
  );
}
