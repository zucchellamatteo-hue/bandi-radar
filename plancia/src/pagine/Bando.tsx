import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Bando as TipoBando, data, dimensione, NOMI_CATEGORIA, NOMI_DECISO_DA, NOMI_RUOLO } from "../api";

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
      {b.pagina_stato === "non_trovata" && (
        <div className="allarme"><b>Bando ufficiale non trovato</b>: niente scheda finché non si trova la pagina del bando.
          <div className="piccolo">{b.pagina_motivo}</div></div>
      )}
      {b.pagina_stato === "trovata" && <p className="piccolo">Pagina ufficiale trovata il {data(b.pagina_cercata_il)}: {b.pagina_motivo}</p>}
      {!b.pagina_stato && <p className="piccolo">Pagina ufficiale non ancora cercata (<code>python -m app.schede.pagina_ufficiale</code>).</p>}
      {b.sintesi && <p className="testo-lungo">{b.sintesi}</p>}
      <CampiAbbinamento b={b} />

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
          <thead><tr><th>Documento</th><th>Che cos'è</th><th>Tipo</th><th>Dimensione</th><th className="nascondi-mobile">Note</th></tr></thead>
          <tbody>{b.allegati.map((a) => (
            <tr key={a.id}>
              <td>{a.ha_file ? <a href={`/api/allegati/${a.id}/file`} target="_blank" rel="noreferrer">{a.nome}</a> : a.nome}
                <div className="piccolo"><a href={a.url} target="_blank" rel="noreferrer">originale ↗</a></div></td>
              <td className="piccolo">{a.categoria ? NOMI_CATEGORIA[a.categoria] || a.categoria : "–"}</td>
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

// I campi che servono all'abbinamento (docs/SCHEDA_BANDO.md), con i tre stati di ogni vincolo.
const ETICHETTE: [string, string][] = [
  ["gestore", "Gestore"], ["territorio_regioni", "Regioni"], ["territorio_province", "Province"], ["territorio_comuni", "Comuni"],
  ["sede_richiesta", "Sede richiesta"], ["soggetti_ammessi", "Soggetti"], ["forme_giuridiche_ammesse", "Forme giuridiche ammesse"],
  ["forme_giuridiche_escluse", "Forme giuridiche escluse"], ["dimensioni_ammesse", "Dimensioni"],
  ["eta_impresa_min_mesi", "Età minima (mesi)"], ["eta_impresa_max_mesi", "Età massima (mesi)"],
  ["requisiti_speciali_obbligatori", "Requisiti obbligatori"], ["requisiti_speciali_premiali", "Requisiti che danno punti"],
  ["codici_ateco", "ATECO ammessi"], ["codici_ateco_esclusi", "ATECO esclusi"], ["ateco_versione", "Versione ATECO"],
  ["regime_aiuto", "Regime d'aiuto"], ["tipi_agevolazione", "Agevolazioni"], ["temi", "Temi"], ["categorie_spesa", "Spese"],
  ["contributo_massimo", "Contributo massimo €"], ["percentuale", "Percentuale"], ["fondo_perduto_massimo", "Fondo perduto massimo €"],
  ["finanziamento_massimo", "Finanziamento massimo €"], ["spesa_minima", "Spesa minima €"], ["spesa_massima", "Spesa massima €"],
  ["dotazione", "Dotazione €"], ["modalita_selezione", "Selezione"], ["ora_scadenza", "Ora di scadenza"], ["stato", "Stato (calcolato)"],
];
const NOMI_COMPLETEZZA: Record<string, string> = {
  bando_ufficiale: "scheda fatta sul bando ufficiale", solo_sintesi: "scheda fatta solo su una sintesi: da verificare",
  nessun_documento: "nessun documento letto",
};

function valore(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  if (Array.isArray(v)) return v.length ? v.join(", ") : null;
  if (typeof v === "number") return v.toLocaleString("it-IT");
  return String(v);
}

function CampiAbbinamento({ b }: { b: TipoBando }) {
  const righe = ETICHETTE.map(([k, e]) => [e, valore(b[k])] as const).filter(([, v]) => v);
  if (!b.completezza && righe.length === 0) return null;
  return (
    <>
      <h2>Campi per l'abbinamento</h2>
      {b.completezza && <p className="piccolo">{NOMI_COMPLETEZZA[b.completezza]}</p>}
      <table><tbody>{righe.map(([e, v]) => <tr key={e}><th>{e}</th><td>{v}</td></tr>)}</tbody></table>
      {b.vincoli && <p className="piccolo">Vincoli: {Object.entries(b.vincoli).map(([k, v]) =>
        `${k.replace("_", " ")} ${v === "vincolo" ? "✔ limitato" : v === "nessun_vincolo" ? "— libero" : "? non noto"}`).join(" · ")}</p>}
      {b.linee && b.linee.length > 0 && (
        <><h2>Linee del bando</h2><ul>{b.linee.map((l) => (
          <li key={l.nome}><b>{l.nome}</b>{l.a_chi_si_rivolge ? `: ${l.a_chi_si_rivolge}` : ""}
            {l.contributo_massimo ? ` — fino a ${l.contributo_massimo.toLocaleString("it-IT")} €` : ""}</li>))}</ul></>
      )}
    </>
  );
}
