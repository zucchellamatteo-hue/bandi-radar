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
