// Chiamate all'API della plancia. Il browser manda da solo le credenziali dell'autenticazione base.

export type Colore = "verde" | "giallo" | "rosso" | "pausa";

export interface Fonte {
  id: string; nome: string; ente: string; tipo: string; territorio: string; url: string | null;
  modalita: string; frequenza: string; stato: string; in_pausa: boolean; piattaforma: string | null;
  colore: Colore; motivo: string; silenzio_giorni: number | null; soglia_silenzio_giorni: number;
  ultimo_controllo: string | null; ultimo_esito: string | null; ultimo_messaggio: string | null;
  ultima_novita: string | null; ultimo_titolo: string | null; novita_30: number; novita_90: number;
}

export type Esito = "rilevante" | "non_rilevante" | "da_rivedere";

export interface Annuncio {
  id: number; fonte_id: string; fonte: string; ente: string; tipo: string; territorio: string;
  url: string; titolo: string; riassunto: string | null; pubblicato_il: string | null; trovato_il: string;
  scadenza?: string | null;
  smistamento?: Esito | null; smistamento_da?: string | null; smistamento_motivo?: string | null; n_allegati?: number;
  bando_id?: number | null; ruolo?: Ruolo | null; collegato_da?: string | null; collegamento_motivo?: string | null;
}

export type Ruolo = "origine" | "doppione" | "proroga" | "rettifica" | "graduatoria" | "faq" | "chiusura";

export const NOMI_RUOLO: Record<Ruolo, string> = {
  origine: "origine", doppione: "stesso bando da un'altra pagina", proroga: "proroga", rettifica: "rettifica",
  graduatoria: "graduatoria o esito", faq: "FAQ", chiusura: "chiusura",
};

// Un annuncio collegato a un bando (nella pagina dell'annuncio e in quella del bando).
export interface AnnuncioDelBando {
  id: number; titolo: string; url: string; ruolo: Ruolo | null; collegato_da: string | null;
  collegamento_motivo: string | null; fonte: string; tipo: string; pubblicato_il?: string | null; trovato_il?: string;
}

export interface BandoBreve {
  id: number; titolo: string; ente: string | null; territorio: string | null; url: string | null;
  scadenza: string | null; codice_ufficiale: string | null; versione: number;
  stato?: string | null; completezza?: string | null; sintesi?: string | null;
}

export interface DubbioAnnuncio { id: number; bando_id: number | null; somiglianza: number | null; motivo: string | null; bando_titolo: string | null }

export interface Dubbio {
  id: number; annuncio_id: number; bando_id: number | null; somiglianza: number | null; motivo: string | null;
  titolo: string; url: string; fonte: string; ente: string;
  bando_titolo: string | null; bando_ente: string | null; bando_url: string | null; bando_annunci: number;
}

export interface Bando extends BandoBreve {
  stato: string | null; data_apertura: string | null; sintesi: string | null; url_chiave: string | null;
  pagina_stato: "trovata" | "non_trovata" | null; pagina_motivo: string | null; pagina_cercata_il: string | null;
  completezza: "bando_ufficiale" | "solo_sintesi" | "nessun_documento" | null; vincoli: Record<string, string> | null;
  linee: { nome: string; a_chi_si_rivolge?: string; contributo_massimo?: number | null }[] | null;
  [campo: string]: unknown;
  chiave_titolo: string | null; creato_il: string; aggiornato_il: string;
  annunci: AnnuncioDelBando[]; allegati: Allegato[]; versioni: { versione: number; causa: string | null; salvata_il: string }[];
}

// Esito delle regole di abbinamento (app/abbinamento/regole.py): stesso formato nel catalogo e nei profili.
export type Livello = "compatibile" | "da_verificare" | "escluso";
export interface EsitoRegole {
  livello: Livello; esclusioni: string[]; da_verificare: string[]; punti_a_favore: string[]; da_controllare: string[];
  interessi: number; fuori_zona: boolean;
}

// Una riga del catalogo dei bandi.
export interface BandoRiga {
  id: number; titolo: string; ente: string | null; territorio: string | null; url: string | null;
  stato: string | null; data_apertura: string | null; scadenza: string | null; ora_scadenza: string | null;
  tipo_agevolazione: string | null; tipi_agevolazione: string[] | null; contributo_massimo: number | null;
  percentuale: number | null; fondo_perduto_massimo: number | null; finanziamento_massimo: number | null;
  dotazione: number | null; modalita_selezione: string | null; completezza: string | null; livelli: string[];
  temi: string[] | null; qualita: number | null; sintesi: string; esito: EsitoRegole;
}

export interface RispostaCatalogo {
  totale: number; conteggi: { compatibile: number; da_verificare: number }; pagina: number; per_pagina: number;
  con_scheda: number; senza_scheda: number; bandi: BandoRiga[];
}

// Valori ammessi della scheda (app/schede/campi.py) e territori.
export interface Valori {
  [campo: string]: string[] | Record<string, string>;
  regioni: Record<string, string>; province: Record<string, string>;
}

export interface Smistamento {
  esito: Esito; motivo: string | null; deciso_da: "regole" | "ia" | "matteo"; costo: number | null; deciso_il: string;
  proposta_esito: Esito | null; proposta_motivo: string | null; proposta_da: string | null;
}

export interface Allegato {
  id: number; url: string; nome: string; tipo: string; dimensione: number | null; impronta: string | null;
  scaricato_il: string; errore: string | null; ha_file: boolean; caratteri_testo: number | null;
  categoria?: string | null;
}

// Che documento e': decide l'ordine del testo per la scheda (la modulistica resta fuori).
export const NOMI_CATEGORIA: Record<string, string> = {
  bando: "bando", pagina: "pagina web", faq: "FAQ", decreto: "decreto o delibera", graduatoria: "graduatoria o esiti",
  modulistica: "modulistica (non va alla scheda)", altro: "altro",
};

export interface Riepilogo {
  fonti: Record<Colore, number>; annunci_ultimi_7_giorni: number; annunci_totali: number;
  ultimo_controllo: string | null; allarmi: { fonte_id: string; nome: string; colore: Colore; motivo: string }[];
}

export interface Controllo {
  id: number; iniziato_il: string; durata_ms: number | null; esito: string; codice_http: number | null;
  byte: number | null; messaggio: string | null; elementi_letti: number; novita: number;
}

export interface Settimana { chiave: string; inizio: string; n: number; fonti: number }
export interface SettimanaDettaglio {
  chiave: string; inizio: string; fine: string; totale: number; gruppi: { tipo: string; annunci: Annuncio[] }[];
}

async function chiama<T>(percorso: string, opzioni?: RequestInit): Promise<T> {
  const r = await fetch(percorso, { ...opzioni, headers: { "Content-Type": "application/json", ...(opzioni?.headers || {}) } });
  if (!r.ok) throw new Error(`Errore ${r.status} su ${percorso}`);
  return r.json();
}

export const api = {
  riepilogo: () => chiama<Riepilogo>("/api/riepilogo"),
  fonti: () => chiama<Fonte[]>("/api/fonti"),
  fonte: (id: string) => chiama<{ fonte: Fonte; controlli: Controllo[]; annunci: Annuncio[] }>(`/api/fonti/${id}`),
  pausa: (id: string, in_pausa: boolean) =>
    chiama(`/api/fonti/${id}/pausa`, { method: "POST", body: JSON.stringify({ in_pausa }) }),
  rilancia: (id: string) => chiama<{ stato: string }>(`/api/fonti/${id}/rilancia`, { method: "POST" }),
  annunci: (parametri: Record<string, string>) =>
    chiama<{ totale: number; pagina: number; per_pagina: number; annunci: Annuncio[]; territori: string[] }>(
      "/api/annunci?" + new URLSearchParams(parametri).toString()),
  annuncio: (id: string) =>
    chiama<Omit<Annuncio, "smistamento"> & {
      fonte_url: string | null; smistamento: Smistamento | null; allegati: Allegato[];
      bando: BandoBreve | null; stesso_bando: AnnuncioDelBando[]; dubbi: DubbioAnnuncio[];
    }>(`/api/annunci/${id}`),
  cambiaBando: (id: number, corpo: { azione: "unisci" | "separa"; con_annuncio?: number; bando_id?: number }) =>
    chiama<{ bando_id: number }>(`/api/annunci/${id}/bando`, { method: "POST", body: JSON.stringify(corpo) }),
  dubbi: (pagina: number) =>
    chiama<{ totale: number; pagina: number; per_pagina: number; dubbi: Dubbio[] }>(`/api/dubbi?pagina=${pagina}`),
  decidiDubbio: (id: number, decisione: "stesso" | "diverso") =>
    chiama<{ bando_id: number }>(`/api/dubbi/${id}`, { method: "POST", body: JSON.stringify({ decisione }) }),
  bando: (id: string) => chiama<Bando>(`/api/bandi/${id}`),
  bandi: (parametri: Record<string, string>) =>
    chiama<RispostaCatalogo>("/api/bandi?" + new URLSearchParams(parametri).toString()),
  valori: () => chiama<Valori>("/api/valori"),
  correggiSmistamento: (id: number, esito: Esito) =>
    chiama<{ esito: Esito; deciso_da: string }>(`/api/annunci/${id}/smistamento`, { method: "POST", body: JSON.stringify({ esito }) }),
  settimane: () => chiama<Settimana[]>("/api/novita/settimane"),
  settimana: (chiave: string) => chiama<SettimanaDettaglio>(`/api/novita/settimane/${chiave}`),
};

export const NOMI_TIPO: Record<string, string> = {
  ue: "Unione europea", nazionale: "Nazionali", regione: "Regioni", camera: "Camere di Commercio",
  capoluogo: "Comuni capoluogo", provincia: "Province", fondazione: "Fondazioni", contesto: "Dati di contesto",
};

export const NOMI_ESITO: Record<Esito, string> = {
  rilevante: "Rilevante", non_rilevante: "Non rilevante", da_rivedere: "Da rivedere",
};

export const NOMI_DECISO_DA: Record<string, string> = { regole: "regole", ia: "IA", matteo: "Matteo" };

// Nomi leggibili dei valori della scheda: quelli non elencati si mostrano togliendo i trattini bassi.
export const NOMI_VALORI: Record<string, string> = {
  impresa: "impresa", libero_professionista: "libero professionista", aspirante_imprenditore: "impresa da costituire",
  ente_terzo_settore: "ente del terzo settore", ente_pubblico: "ente pubblico", persona_fisica: "persona fisica",
  ditta_individuale: "ditta individuale", snc: "snc", sas: "sas", srl: "srl", srls: "srl semplificata", spa: "spa",
  sapa: "sapa", societa_semplice: "società semplice", cooperativa: "cooperativa", consorzio: "consorzio",
  rete_imprese: "rete d'imprese", associazione_professionale: "associazione professionale", stp: "società tra professionisti",
  micro: "micro", piccola: "piccola", media: "media", grande: "grande",
  femminile: "femminile", giovanile: "giovanile", startup_innovativa: "startup innovativa", pmi_innovativa: "PMI innovativa",
  artigiana: "artigiana", agricola: "agricola", commerciale: "commerciale", turistica: "turistica",
  impresa_sociale: "impresa sociale", rating_legalita: "rating di legalità",
  certificazione_parita_genere: "certificazione parità di genere", esportatrice: "esportatrice", nuova_impresa: "nuova impresa",
  fondo_perduto: "fondo perduto", credito_imposta: "credito d'imposta", finanziamento_agevolato: "finanziamento agevolato",
  garanzia: "garanzia", voucher: "voucher", servizi: "servizi", premio: "premio", misto: "misto",
  sportello: "a sportello", sportello_valutativo: "sportello valutativo", graduatoria: "graduatoria", click_day: "click day",
  automatica: "automatica", negoziale: "negoziale",
  de_minimis: "de minimis", de_minimis_agricolo: "de minimis agricolo", gber: "GBER (esenzione)", aber: "ABER (agricoltura)",
  temporary_framework: "quadro temporaneo", notificato: "aiuto notificato", non_aiuto: "non è aiuto di Stato",
  avvio_impresa: "avvio d'impresa", internazionalizzazione: "internazionalizzazione",
  macchinari_attrezzature: "macchinari e attrezzature", opere_edili_impianti: "opere edili e impianti",
  software_digitale: "software e digitale", fiere_eventi: "fiere ed eventi", marketing_promozione: "marketing e promozione",
  brevetti_certificazioni: "brevetti e certificazioni", energia_efficienza: "energia ed efficienza",
  scorte_circolante: "scorte e circolante", affitto_gestione: "affitto e gestione", ricerca_sviluppo: "ricerca e sviluppo",
  aperto: "aperto", in_arrivo: "in arrivo", chiuso: "chiuso", altro: "altro",
};
export const nome = (v: string | null | undefined) => (v ? NOMI_VALORI[v] || v.replace(/_/g, " ") : "–");

export function euro(n: number | null | undefined): string {
  if (n == null) return "–";
  return n.toLocaleString("it-IT", { maximumFractionDigits: 0 }) + " €";
}

export function dimensione(byte: number | null | undefined): string {
  if (byte == null) return "–";
  if (byte < 1024 * 1024) return `${Math.max(1, Math.round(byte / 1024))} kB`;
  return `${(byte / 1024 / 1024).toFixed(1)} MB`;
}

export function data(iso: string | null | undefined, conOra = false): string {
  if (!iso) return "–";
  const d = new Date(iso);
  return conOra ? d.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" }) : d.toLocaleDateString("it-IT");
}
