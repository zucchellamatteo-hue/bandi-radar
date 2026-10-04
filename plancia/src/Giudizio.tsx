import { useEffect, useState } from "react";
import { api, data, FeedbackBando, ProblemaFeedback, NOMI_STATO_FEEDBACK } from "./api";

// Campi della scheda a cui si puo' riferire un problema (facoltativo).
export const CAMPI_SCHEDA: Record<string, string> = {
  stato: "stato", scadenza: "scadenza", data_apertura: "apertura", chiuso_il: "data di chiusura",
  a_chi_si_rivolge: "a chi si rivolge", soggetti_ammessi: "soggetti ammessi", forme_giuridiche_ammesse: "forme giuridiche",
  dimensioni_ammesse: "dimensioni", territorio_regioni: "regioni", territorio_province: "province", territorio_comuni: "comuni",
  codici_ateco: "ATECO ammessi", codici_ateco_esclusi: "ATECO esclusi", contributo_massimo: "contributo massimo",
  percentuale: "percentuale", fondo_perduto_massimo: "fondo perduto massimo", finanziamento_massimo: "prestito massimo",
  tipi_agevolazione: "tipo di agevolazione", forma_incentivo: "forma dell'incentivo", spese_ammesse: "spese ammesse",
  cosa_finanzia: "cosa finanzia", requisiti: "requisiti", sintesi: "sintesi", dotazione: "dotazione",
  modalita_selezione: "modalità di selezione", documenti: "documenti",
};

// Voto e problemi sulla scheda (revisori e amministratori). Un giudizio per persona e versione, si puo' cambiare.
export default function Giudizio({ bandoId, admin, perImpresa }: { bandoId: number; admin: boolean; perImpresa?: boolean }) {
  const [fb, setFb] = useState<FeedbackBando | null>(null);
  const [voto, setVoto] = useState<number | null>(null);
  const [problemi, setProblemi] = useState<ProblemaFeedback[]>([]);
  const [commento, setCommento] = useState("");
  const [esito, setEsito] = useState<string | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  const carica = () => api.feedbackBando(bandoId).then((r) => {
    setFb(r);
    const mio = r.mio && r.mio.versione === r.versione ? r.mio : null;
    setVoto(mio?.voto ?? null); setProblemi(mio?.problemi ?? []); setCommento(mio?.commento ?? "");
  }).catch((e) => setErrore(String(e.message || e)));
  useEffect(() => { carica(); }, [bandoId]);
  if (!fb) return errore ? <div className="allarme">{errore}</div> : null;

  const cambia = (i: number, campo: keyof ProblemaFeedback, valore: string) =>
    setProblemi(problemi.map((p, j) => (j === i ? { ...p, [campo]: valore || null } : p)));
  const salva = async () => {
    setErrore(null); setEsito(null);
    try {
      await api.giudica(bandoId, { voto, problemi, commento: commento || null });
      setEsito("Giudizio salvato, grazie."); carica();
    } catch (e) { setErrore(e instanceof Error ? e.message : String(e)); }
  };
  const vecchio = fb.mio && fb.mio.versione !== fb.versione ? fb.mio : null;

  return (
    <div className="giudizio" id="giudizio">
      <h2>{perImpresa ? "Ti è utile questa scheda? Hai trovato un errore?" : "Il tuo giudizio sulla scheda"}</h2>
      {vecchio && <p className="piccolo">Avevi giudicato la versione {vecchio.versione} (voto {vecchio.voto ?? "–"}): la scheda è
        cambiata, il giudizio va rifatto sulla versione {fb.versione}.</p>}
      {fb.mio && fb.mio.versione === fb.versione && fb.mio.stato !== "nuovo" && (
        <div className="avviso">Stato della tua segnalazione: <b>{NOMI_STATO_FEEDBACK[fb.mio.stato]}</b>
          {fb.mio.risposta && <> — {fb.mio.risposta}</>}</div>)}
      <div className="voto">
        <span>{perImpresa ? "Quanto è chiara e utile?" : "Mi fiderei a proporlo a un cliente?"}</span>
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" className={voto != null && n <= voto ? "stella piena" : "stella"} title={`${n} su 5`}
            onClick={() => setVoto(voto === n ? null : n)}>★</button>))}
        <span className="piccolo">{voto ? ["", "no", "poco", "con controlli", "quasi", "sì"][voto] : "nessun voto"}</span>
      </div>
      {problemi.map((p, i) => (
        <div key={i} className="problema">
          <select value={p.categoria} onChange={(e) => cambia(i, "categoria", e.target.value)}>
            {Object.entries(fb.categorie).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={p.campo || ""} onChange={(e) => cambia(i, "campo", e.target.value)}>
            <option value="">campo (facoltativo)</option>
            {Object.entries(CAMPI_SCHEDA).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <input type="text" placeholder="cosa non va (e, se puoi, dove lo dice il bando)" value={p.testo || ""}
            onChange={(e) => cambia(i, "testo", e.target.value)} />
          <button type="button" onClick={() => setProblemi(problemi.filter((_, j) => j !== i))}>Togli</button>
        </div>
      ))}
      <p><button type="button" onClick={() => setProblemi([...problemi, { categoria: "stato_sbagliato", campo: null, testo: null }])}>
        + Segnala un problema</button></p>
      <textarea placeholder="Commento libero (facoltativo)" value={commento} onChange={(e) => setCommento(e.target.value)} rows={2} />
      {errore && <div className="allarme">{errore}</div>}
      {esito && <div className="avviso">{esito}</div>}
      <p><button type="button" className="primario" onClick={salva}>Salva il giudizio</button></p>

      {admin && fb.tutti.length > 0 && (
        <>
          <h3>Giudizi ricevuti su questa scheda</h3>
          <table>
            <thead><tr><th>Chi</th><th>Versione</th><th>Voto</th><th>Problemi</th><th>Stato</th></tr></thead>
            <tbody>{fb.tutti.map((f) => (
              <tr key={f.id}>
                <td>{f.nome || f.email}<div className="piccolo">{f.ruolo} · {data(f.aggiornato_il, true)}</div></td>
                <td>{f.versione}</td>
                <td>{f.voto ?? "–"}</td>
                <td>{f.problemi.map((p, i) => <div key={i}><b>{fb.categorie[p.categoria]}</b>{p.campo ? ` (${CAMPI_SCHEDA[p.campo] || p.campo})` : ""}{p.testo ? `: ${p.testo}` : ""}</div>)}
                  {f.commento && <div className="piccolo">{f.commento}</div>}</td>
                <td>{NOMI_STATO_FEEDBACK[f.stato]}{f.risposta && <div className="piccolo">{f.risposta}</div>}</td>
              </tr>))}</tbody>
          </table>
        </>
      )}
    </div>
  );
}
