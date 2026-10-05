import { ReactNode, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Bando as TipoBando, FormaIncentivo as TipoForma, data, dimensione, euro, nome, NOMI_CATEGORIA, NOMI_DECISO_DA, NOMI_RUOLO } from "../api";
import { Importo } from "./Catalogo";
import { puo, useUtente } from "../utente";
import Giudizio from "../Giudizio";

// La scheda completa del bando (docs/SCHEDA_BANDO.md), i documenti, gli annunci che ne parlano e le versioni.
export default function Bando() {
  const { id } = useParams();
  const [b, setB] = useState<TipoBando | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const utente = useUtente();
  const admin = puo(utente, "lavoro");
  const giudica = puo(utente, "giudizi");
  useEffect(() => { if (id) api.bando(id).then(setB).catch((e) => setErrore(String(e))); }, [id]);
  if (errore) return <div className="allarme">{errore}</div>;
  if (!b) return <div className="caricamento">Caricamento…</div>;
  const dati = (b.dati || {}) as { avvertenze?: string[]; problemi?: string[]; modello?: string };
  const documenti = b.allegati.filter((a) => a.ha_file);
  const mancati = b.allegati.filter((a) => !a.ha_file);
  return (
    <>
      <p><Link to="/catalogo">← Catalogo</Link></p>
      <h1>{b.titolo}</h1>
      <p><span className={`stato-bando ${b.stato || "non_noto"}`}>{b.stato ? nome(b.stato) : "stato non noto"}</span>
        <span className="piccolo"> · {b.ente}{b.gestore && b.gestore !== b.ente ? ` (gestisce ${b.gestore})` : ""}
          {b.codice_ufficiale ? ` · codice ${b.codice_ufficiale}` : ""} · versione {b.versione}</span>
        {b.completezza && <> · <a href="#giudizio">giudica la scheda ↓</a></>}</p>
      <p>{b.data_apertura && <>apre il <b>{data(b.data_apertura)}</b>{b.ora_apertura ? ` ore ${String(b.ora_apertura).slice(0, 5)}` : ""} · </>}
        {b.scadenza ? <>scade il <b className="scadenza">{data(b.scadenza)}</b>{b.ora_scadenza ? ` ore ${String(b.ora_scadenza).slice(0, 5)}` : ""}</>
          : "nessuna scadenza scritta"}
        {b.chiuso_il ? <> · <b>chiuso il {data(String(b.chiuso_il))}</b></> : null}
        {b.modalita_selezione ? ` · ${nome(String(b.modalita_selezione))}` : ""}
        {b.url && <> · <a href={b.url} target="_blank" rel="noreferrer">pagina ufficiale ↗</a></>}</p>

      {b.pagina_stato === "non_trovata" && (
        <div className="allarme"><b>Bando ufficiale non trovato</b>: niente scheda finché non si trova la pagina del bando.
          <div className="piccolo">{b.pagina_motivo}</div></div>
      )}
      {!b.completezza && b.pagina_stato !== "non_trovata" && <div className="avviso">Scheda non ancora fatta.</div>}
      {b.documentazione ? <p className="piccolo">Documenti: <b>{b.documentazione === "bando" ? "c'è il testo del bando"
        : b.documentazione === "sintesi" ? "solo sintesi o pagine web (in disparte)" : "nessun documento leggibile (in disparte)"}</b>
        {b.documentazione_motivo ? ` — ${String(b.documentazione_motivo)}` : ""}</p> : null}
      {b.completezza && b.completezza !== "bando_ufficiale" && (
        <div className="avviso"><b>{NOMI_COMPLETEZZA[b.completezza]}</b>: i dati vanno controllati sul bando ufficiale.</div>
      )}

      {b.completezza && (
        <div className="scheda-griglia">
          <div className="riquadro"><div className="etichetta">Agevolazione</div>
            {((b.tipi_agevolazione as string[] | null) || [b.tipo_agevolazione]).filter(Boolean).map((t) =>
              <span key={String(t)} className="etichetta-tipo">{nome(String(t))}</span>)}
            <Importo b={b as never} /></div>
          {b.fondo_perduto_massimo != null && b.fondo_perduto_massimo !== b.contributo_massimo && <Riquadro etichetta="di cui a fondo perduto" valore={euro(b.fondo_perduto_massimo as number)}
            nota={b.percentuale_fondo_perduto != null ? `${b.percentuale_fondo_perduto}% delle spese` : undefined} />}
          {b.finanziamento_massimo != null && <Riquadro etichetta="Prestito fino a" valore={euro(b.finanziamento_massimo as number)} />}
          {(b.spesa_minima != null || b.spesa_massima != null) && <Riquadro etichetta="Progetto ammesso"
            valore={`${b.spesa_minima != null ? "da " + euro(b.spesa_minima as number) : ""}${b.spesa_massima != null ? " a " + euro(b.spesa_massima as number) : ""}`} />}
          {b.dotazione != null && <Riquadro etichetta="Dotazione del bando" valore={euro(b.dotazione as number)} />}
        </div>
      )}
      {b.sintesi && <p className="testo-lungo">{b.sintesi}</p>}
      <FormaIncentivo f={b.forma_incentivo} />

      <Testo titolo="A chi si rivolge" testo={b.a_chi_si_rivolge} />
      <Testo titolo="Cosa finanzia" testo={b.cosa_finanzia} />
      <Testo titolo="Spese ammesse" testo={b.spese_ammesse} />
      <Testo titolo="Requisiti" testo={b.requisiti} />
      <Vincoli b={b} />
      <Linee b={b} />
      <Dettagli b={b} />
      {(dati.avvertenze?.length || dati.problemi?.length) ? (
        <>
          <h2>Avvertenze sulla scheda</h2>
          <ul className="motivi da_verificare">{[...(dati.avvertenze || []), ...(dati.problemi || [])].map((a, i) => <li key={i}>{a}</li>)}</ul>
          {dati.modello && <p className="piccolo">Scheda scritta da: {dati.modello}</p>}
        </>
      ) : null}

      {b.completezza && (giudica || admin) && <Giudizio bandoId={b.id} admin={admin} />}

      <h2>Documenti del bando</h2>
      {documenti.length === 0 ? <p className="piccolo">Nessun documento scaricato.</p> : (
        <table>
          <thead><tr><th>Documento</th><th>Che cos'è</th><th>Tipo</th><th>Dimensione</th><th className="nascondi-mobile">Testo letto</th></tr></thead>
          <tbody>{documenti.map((a) => (
            <tr key={a.id}>
              <td><a href={`/api/allegati/${a.id}/file`} target="_blank" rel="noreferrer">{a.nome}</a>
                <div className="piccolo"><a href={a.url} target="_blank" rel="noreferrer">originale ↗</a> · scaricato il {data(a.scaricato_il)}</div></td>
              <td className="piccolo">{a.categoria ? NOMI_CATEGORIA[a.categoria] || a.categoria : "–"}</td>
              <td>{a.tipo === "faq" ? "FAQ" : a.tipo === "pagina" ? "pagina web" : a.tipo.toUpperCase()}</td>
              <td>{dimensione(a.dimensione)}</td>
              <td className="nascondi-mobile piccolo">{a.caratteri_testo ? `${a.caratteri_testo.toLocaleString("it-IT")} caratteri` : "nessun testo letto"}</td>
            </tr>
          ))}</tbody>
        </table>
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

      <h2>Annunci che parlano di questo bando</h2>
      <table>
        <thead><tr><th>Annuncio</th><th>Ruolo</th><th className="nascondi-mobile">Fonte</th><th className="nascondi-mobile">Trovato</th></tr></thead>
        <tbody>{b.annunci.map((a) => (
          <tr key={a.id}>
            <td>{admin ? <Link to={`/annunci/${a.id}`}>{a.titolo}</Link> : a.titolo} <a href={a.url} target="_blank" rel="noreferrer" className="piccolo">originale ↗</a></td>
            <td>{a.ruolo ? NOMI_RUOLO[a.ruolo] : "–"}
              <div className="piccolo">{a.collegato_da ? `da ${NOMI_DECISO_DA[a.collegato_da] || a.collegato_da}` : ""}{a.collegamento_motivo ? `: ${a.collegamento_motivo}` : ""}</div></td>
            <td className="nascondi-mobile piccolo">{a.fonte}</td>
            <td className="nascondi-mobile piccolo">{data(a.pubblicato_il || a.trovato_il)}</td>
          </tr>
        ))}</tbody>
      </table>
      {b.pagina_stato === "trovata" && <p className="piccolo">Pagina ufficiale trovata il {data(b.pagina_cercata_il)}: {b.pagina_motivo}</p>}

      {b.versioni.length > 0 && (
        <>
          <h2>Versioni precedenti</h2>
          <ul>{b.versioni.map((v) => <li key={v.versione} className="piccolo">versione {v.versione}, fino al {data(v.salvata_il, true)}{v.causa ? ` — ${v.causa}` : ""}</li>)}</ul>
        </>
      )}
    </>
  );
}

const NOMI_COMPLETEZZA: Record<string, string> = {
  bando_ufficiale: "scheda fatta sul bando ufficiale", solo_sintesi: "Scheda fatta solo su una sintesi",
  nessun_documento: "Scheda fatta senza documenti",
};

function Riquadro({ etichetta, valore, nota }: { etichetta: string; valore: string; nota?: string }) {
  return <div className="riquadro"><div className="etichetta">{etichetta}</div><div className="numero">{valore}</div>
    {nota && <div className="piccolo">{nota}</div>}</div>;
}

function Testo({ titolo, testo }: { titolo: string; testo: unknown }) {
  if (!testo) return null;
  return <><h2>{titolo}</h2><p className="testo-lungo">{String(testo)}</p></>;
}

function elenco(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  if (Array.isArray(v)) return v.length ? v.map((x) => nome(String(x))).join(", ") : null;
  if (typeof v === "number") return v.toLocaleString("it-IT");
  return nome(String(v));
}

// Ogni vincolo con il suo stato (vincolo / nessun vincolo / non noto) e i valori della scheda.
const VINCOLI: [string, string, (b: TipoBando) => ReactNode][] = [
  ["territorio", "Territorio", (b) => [elenco(b.territorio_regioni), elenco(b.territorio_province), elenco(b.territorio_comuni)]
    .filter(Boolean).join(" · ") + (b.sede_richiesta ? ` (sede ${nome(String(b.sede_richiesta)).replace("legale o operativa", "legale o operativa")})` : "")
    + (b.territorio ? ` — ${b.territorio}` : "")],
  ["soggetti", "Chi può partecipare", (b) => elenco(b.soggetti_ammessi)],
  ["forme_giuridiche", "Forma giuridica", (b) => [b.forme_giuridiche_ammesse && elenco(b.forme_giuridiche_ammesse) && `ammesse: ${elenco(b.forme_giuridiche_ammesse)}`,
    elenco(b.forme_giuridiche_escluse) && `escluse: ${elenco(b.forme_giuridiche_escluse)}`].filter(Boolean).join(" · ")],
  ["dimensioni", "Dimensione", (b) => elenco(b.dimensioni_ammesse)],
  ["ateco", "Settori (ATECO)", (b) => [elenco(b.codici_ateco) && `ammessi: ${(b.codici_ateco as string[]).join(", ")}`,
    elenco(b.codici_ateco_esclusi) && `esclusi: ${(b.codici_ateco_esclusi as string[]).join(", ")}`,
    b.ateco_versione ? `versione ${b.ateco_versione}` : null].filter(Boolean).join(" · ")],
  ["eta_impresa", "Età dell'impresa", (b) => [b.eta_impresa_min_mesi != null && `almeno ${b.eta_impresa_min_mesi} mesi`,
    b.eta_impresa_max_mesi != null && `al massimo ${b.eta_impresa_max_mesi} mesi`].filter(Boolean).join(", ")],
  ["requisiti_speciali", "Requisiti speciali", (b) => [elenco(b.requisiti_speciali_obbligatori) && `obbligatori: ${elenco(b.requisiti_speciali_obbligatori)}`,
    elenco(b.requisiti_speciali_premiali) && `danno punti: ${elenco(b.requisiti_speciali_premiali)}`].filter(Boolean).join(" · ")],
  ["dipendenti", "Dipendenti", (b) => [b.dipendenti_min != null && `da ${b.dipendenti_min}`, b.dipendenti_max != null && `a ${b.dipendenti_max}`].filter(Boolean).join(" ")],
  ["fatturato", "Fatturato", (b) => [b.fatturato_min != null && `da ${euro(b.fatturato_min as number)}`, b.fatturato_max != null && `a ${euro(b.fatturato_max as number)}`].filter(Boolean).join(" ")],
  ["spesa", "Importo del progetto", (b) => [b.spesa_minima != null && `da ${euro(b.spesa_minima as number)}`, b.spesa_massima != null && `a ${euro(b.spesa_massima as number)}`].filter(Boolean).join(" ")],
  ["regime_aiuto", "Regime d'aiuto", (b) => elenco(b.regime_aiuto)],
];
const STATI: Record<string, string> = { vincolo: "✔ limitato", nessun_vincolo: "— nessun limite", non_noto: "? non noto" };

function Vincoli({ b }: { b: TipoBando }) {
  if (!b.completezza) return null;
  const vincoli = b.vincoli || {};
  return (
    <>
      <h2>Chi può partecipare: i vincoli</h2>
      <table className="vincoli"><tbody>{VINCOLI.map(([chiave, etichetta, valore]) => {
        const stato = vincoli[chiave] || "non_noto";
        return <tr key={chiave}><th>{etichetta}</th><td className={`stato ${stato}`}>{STATI[stato] || stato}</td><td>{valore(b) || ""}</td></tr>;
      })}</tbody></table>
      <p className="piccolo">"Limitato": il bando pone un limite. "Nessun limite": il bando dice che non ce ne sono. "Non noto": la scheda non lo sa (per esempio perché fatta su una sintesi): da verificare sul bando.</p>
    </>
  );
}

// Forma dell'incentivo (richiesta di Matteo del 02/10): che aiuto e', in che quota e fino a quanto, per chi.
const NOMI_FORMA: Record<string, string> = {
  fondo_perduto: "Fondo perduto", finanziamento_agevolato: "Finanziamento agevolato", credito_imposta: "Credito d'imposta",
  garanzia: "Garanzia", voucher: "Voucher", servizi: "Servizi gratuiti", premio: "Premio",
  contributo_interessi: "Contributo in conto interessi", altro: "Altra forma",
};

function FormaIncentivo({ f }: { f: TipoForma | null }) {
  if (!f || !f.righe?.length) return null;
  const forme = [...new Set(f.righe.flatMap((r) => r.forme.map((x) => x.forma)))];
  const conSpesa = f.righe.some((r) => r.spesa_minima != null || r.spesa_massima != null);
  const conMassima = f.righe.some((r) => r.agevolazione_massima != null);
  const conNote = f.righe.some((r) => r.note);
  const spesa = (r: TipoForma["righe"][number]) =>
    `${r.spesa_minima != null ? "da " + euro(r.spesa_minima) : ""}${r.spesa_massima != null ? " a " + euro(r.spesa_massima) : ""}`.trim() || "—";
  return (
    <section className="forma-incentivo">
      <h2>Forma dell'incentivo</h2>
      <div className="forma-chip">{forme.map((x) => <span key={x} className={`chip-forma ${x}`}>{NOMI_FORMA[x] || x}</span>)}</div>
      {f.descrizione && <p className="forma-descrizione">{f.descrizione}</p>}
      <table className="tabella-forma">
        <thead><tr><th>Per chi</th>{forme.map((x) => <th key={x}>{NOMI_FORMA[x] || x}</th>)}
          {conSpesa && <th>Progetto ammesso</th>}{conMassima && <th>Agevolazione massima</th>}{conNote && <th>Note</th>}</tr></thead>
        <tbody>{f.righe.map((r, i) => (
          <tr key={i}>
            <td><b>{r.per_chi}</b></td>
            {forme.map((x) => {
              const c = r.forme.find((y) => y.forma === x);
              if (!c) return <td key={x} className="piccolo">—</td>;
              return (
                <td key={x}>
                  {c.percentuale != null && <div className="forma-percentuale">{c.percentuale}%{x === "garanzia" ? "" : " della spesa"}</div>}
                  {c.massimale != null && <div>fino a <b>{euro(c.massimale)}</b></div>}
                  {c.percentuale == null && c.massimale == null && !c.condizioni && <div className="piccolo">sì</div>}
                  {c.condizioni && <div className="piccolo">{c.condizioni}</div>}
                </td>
              );
            })}
            {conSpesa && <td>{spesa(r)}</td>}
            {conMassima && <td>{r.agevolazione_massima != null ? euro(r.agevolazione_massima) : "—"}</td>}
            {conNote && <td className="piccolo">{r.note}</td>}
          </tr>
        ))}</tbody>
      </table>
      {f.note && <p className="piccolo">{f.note}</p>}
      {f.ricavata && <p className="piccolo">Ricavata dai campi della scheda: sarà compilata dai documenti al prossimo aggiornamento della scheda.</p>}
    </section>
  );
}

function Linee({ b }: { b: TipoBando }) {
  if (!b.linee || b.linee.length === 0) return null;
  return (
    <>
      <h2>Linee del bando</h2>
      <table><tbody>{b.linee.map((l) => {
        const riga = l as Record<string, unknown>;
        const altri = Object.entries(riga).filter(([k, v]) => !["nome", "a_chi_si_rivolge"].includes(k) && elenco(v))
          .map(([k, v]) => `${k.replace(/_/g, " ")}: ${k.includes("massimo") || k.includes("spesa") ? euro(v as number) : elenco(v)}`);
        return <tr key={l.nome}><th>{l.nome}</th><td>{l.a_chi_si_rivolge}<div className="piccolo">{altri.join(" · ")}</div></td></tr>;
      })}</tbody></table>
    </>
  );
}

// I sei blocchi di dettagli per il commercialista: si mostrano solo le voci compilate.
const BLOCCHI: [string, string][] = [["intensita", "Intensità dell'aiuto"], ["finanziamento", "Prestito e garanzie"],
  ["vincoli_spese", "Vincoli sulle spese"], ["esclusioni", "Esclusioni"], ["obblighi", "Obblighi ed erogazione"], ["domanda", "Come si presenta la domanda"]];

function voce(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  if (Array.isArray(v)) {
    const parti = v.map((x) => (typeof x === "object" && x ? Object.values(x as object).filter((y) => y !== null && y !== "").map((y) => nome(String(y))).join(" – ") : nome(String(x))));
    return parti.filter(Boolean).join("; ") || null;
  }
  if (typeof v === "object") {
    const o = v as Record<string, unknown>;
    if ("stato" in o) return o.stato === "vincolo" || o.dettaglio ? `${STATI[String(o.stato)] || o.stato}${o.dettaglio ? `: ${o.dettaglio}` : ""}` : null;
    const parti = Object.entries(o).filter(([, x]) => x !== null && x !== "").map(([k, x]) => `${nome(k)} ${x}%`);
    return parti.join(", ") || null;
  }
  return typeof v === "number" ? v.toLocaleString("it-IT") : String(v);
}

function Dettagli({ b }: { b: TipoBando }) {
  const blocchi = BLOCCHI.map(([chiave, titolo]) => {
    const righe = Object.entries((b[chiave] || {}) as Record<string, unknown>).map(([k, v]) => [k, voce(v)] as const).filter(([, v]) => v);
    return { chiave, titolo, righe };
  }).filter((x) => x.righe.length);
  if (!blocchi.length) return null;
  return (
    <>
      <h2>Dettagli per il commercialista</h2>
      {blocchi.map(({ chiave, titolo, righe }) => (
        <details key={chiave} open={chiave === "intensita" || chiave === "domanda"}>
          <summary><b>{titolo}</b></summary>
          <table><tbody>{righe.map(([k, v]) => <tr key={k}><th>{k.replace(/_/g, " ")}</th><td>{v}</td></tr>)}</tbody></table>
        </details>
      ))}
    </>
  );
}
