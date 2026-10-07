// Chiamate all'API della plancia. Il browser manda da solo il cookie della sessione (accesso con email e password).

export type RuoloUtente = "admin" | "revisore" | "impresa";
export interface Utente {
  id: number; email: string; nome: string | null; ruolo: RuoloUtente; attivo?: boolean;
  creato_il?: string; ultimo_accesso?: string | null; password_impostata?: boolean; permessi: string[];
}
// Feedback sulle schede (app/feedback): voto 1-5 e problemi.
export type StatoFeedback = "nuovo" | "preso_in_carico" | "corretto" | "respinto";
export const NOMI_STATO_FEEDBACK: Record<StatoFeedback, string> = {
  nuovo: "nuovo", preso_in_carico: "preso in carico", corretto: "corretto", respinto: "respinto",
};
export interface ProblemaFeedback { categoria: string; campo: string | null; testo: string | null }
export interface GiudizioSalvato {
  id: number; bando_id: number; versione: number; ruolo: RuoloUtente; voto: number | null; problemi: ProblemaFeedback[];
  commento: string | null; stato: StatoFeedback; risposta: string | null; aggiornato_il: string;
  gestito_da: string | null; gestito_il: string | null; analisi: { regola?: string | null } | null;
}
export interface FeedbackBando {
  versione: number; mio: GiudizioSalvato | null; categorie: Record<string, string>;
  tutti: (GiudizioSalvato & { email: string; nome: string | null })[];
}
export interface RigaFeedback extends GiudizioSalvato {
  email: string; nome: string | null; titolo: string; ente: string | null; versione_attuale: number; qualita: number | null; peso: number;
}
// Segnalazioni rapide (app/segnalazioni): il pulsante "Segnala" in ogni pagina.
export type StatoSegnalazione = "nuova" | "presa_in_carico" | "risolta" | "respinta";
export interface TipoSegnalazione { nome: string; descrizione: string; campi: Record<string, string> }
export interface Segnalazione {
  id: number; tipo: string; testo: string | null; dettagli: Record<string, string>; bando_id: number | null; pagina: string | null;
  utente_id: number | null; ruolo: RuoloUtente | null; stato: StatoSegnalazione; risposta: string | null; creata_il: string;
  gestita_il: string | null; gestita_da: string | null; email?: string | null; nome?: string | null; bando_titolo?: string | null;
}
// Area impresa (app/impresa).
export interface Impresa {
  id: number; nome: string; profilo_codice: string; profilo: Profilo; fasce: { dipendenti?: string; fatturato?: string };
  email_settimanale: boolean; sedi: number; creata_il: string;
}
export interface SchedaRidotta {
  id: number; titolo: string; ente: string | null; territorio: string | null; url: string | null; stato: string | null;
  data_apertura: string | null; ora_apertura: string | null; scadenza: string | null; ora_scadenza: string | null; chiuso_il: string | null;
  sintesi: string | null; a_chi_si_rivolge: string | null; cosa_finanzia: string | null; spese_ammesse: string | null; requisiti: string | null;
  tipi_agevolazione: string[] | null; tipo_agevolazione: string | null; contributo_massimo: number | null; percentuale: number | null;
  fondo_perduto_massimo: number | null; finanziamento_massimo: number | null; spesa_minima: number | null; spesa_massima: number | null;
  dotazione: number | null; modalita_selezione: string | null; forma_incentivo: FormaIncentivo | null; versione: number;
  percentuale_fondo_perduto?: number | null; agevolazione?: string;
  imprese: { id: number; nome: string; esito: EsitoRegole; motivo?: string; da_verificare_semplici?: string[] }[]; documenti_ufficiali: { nome: string; url: string }[]; avvertenza: string;
  misure_cumulabili?: MisuraBreve[];
  vincoli_spese?: Record<string, { stato?: string; dettaglio?: string } | null> | null;
}
// Pagina "I miei bandi" (07/10): bandi in tre gruppi, riepilogo, misure nazionali utili al profilo (app/impresa/vista.py).
export type GruppoImpresa = "adatti" | "da_valutare" | "altre_regioni";
export interface BandoImpresa extends BandoRiga {
  gruppo: GruppoImpresa; agevolazione: string; fondo_perduto: boolean; motivo: string; da_verificare_semplici: string[];
  giorni_alla_scadenza: number | null; in_scadenza: boolean; nuovo: boolean;
}
export interface MisuraPerProfilo extends MisuraBreve { sintesi: string; esempio: { testo: string; interesse: Interesse } | null }
export interface VistaImpresa {
  impresa: { id: number | null; nome: string; codice?: string };
  conteggi: { adatti: number; da_valutare: number; altre_regioni: number; in_scadenza: number; nuovi: number; compatibile: number; da_verificare: number };
  bandi: BandoImpresa[]; misure: { tipo: { id: string; nome: string } | null; misure: MisuraPerProfilo[] };
  giorni_in_scadenza: number; giorni_nuovo: number; avvertenza: string; bloccato?: boolean;
}
export type StatoRichiesta = "nuova" | "in_corso" | "accettata" | "chiusa";
export const NOMI_STATO_RICHIESTA: Record<StatoRichiesta, string> = { nuova: "ricevuta", in_corso: "in valutazione", accettata: "accettata", chiusa: "chiusa" };
export interface RichiestaSupporto {
  id: number; bando_id: number; impresa_id: number; messaggio: string | null; stato: StatoRichiesta; creata_il: string;
  bando_titolo: string; impresa_nome: string; email?: string; utente_nome?: string | null; nota?: string | null; bando_scadenza?: string | null; origine?: string;
}
export interface EmailImpresa {
  id: number; impresa_id: number; impresa_nome?: string; utente_email?: string; settimana: string; oggetto: string; testo: string;
  html: string | null; stato: string; creata_il: string; decisa_il: string | null; decisa_da: string | null; errore: string | null;
  n_bandi?: number; bandi?: { bando_id: number; motivo: string }[];
}
export interface ImpresaIscritta {
  id: number; nome: string; email_settimanale: boolean; creata_il: string; email: string; utente_nome: string | null;
  attivo: boolean; sedi: number; richieste: number; profilo_codice?: string;
}

// Abbonamenti (app/abbonamenti).
export interface Abbonamento {
  stato: "prova" | "attivo" | "in_ritardo" | "disdetto" | "gratuito"; piano: "mensile" | "annuale" | null; accesso: boolean;
  attivi: boolean; giorni_prova: number | null; prova_fino_al: string | null; fine_impegno: string | null; fine_periodo: string | null;
  imprese_extra: number; sedi_extra: number; prezzi: { mensile: number; annuale: number; impresa: number; sede: number };
  iva_inclusa: boolean; stripe: boolean; portale: boolean;
}
export interface RigaAbbonamento {
  utente_id: number; email: string; nome: string | null; stato: string | null; piano: string | null; prova_fino_al: string | null;
  fine_impegno: string | null; fine_periodo: string | null; imprese_extra: number | null; sedi_extra: number | null; nota: string | null; imprese: number;
}
export const NOMI_STATO_ABBONAMENTO: Record<string, string> = {
  prova: "in prova", attivo: "attivo", in_ritardo: "pagamento in ritardo", disdetto: "disdetto", gratuito: "gratuito",
};

// Misure nazionali sugli investimenti (app/misure/misure.yaml): conto termico, iperammortamento...
export interface MisuraBreve {
  id: string; nome: string; tipo: string | null; ente: string | null; beneficio_min: number | null; beneficio_max: number | null;
  nota_beneficio: string | null; cumulo: string | null; url_ufficiale: string | null; spese_in_comune?: string[];
}
// Esempi pratici per tipo di impresa (profili_esempio in testa a misure.yaml), gia' ordinati per interesse.
export type Interesse = "alto" | "medio" | "basso" | "nullo";
export interface ProfiloEsempio { id: string; nome: string; descrizione?: string }
export interface EsempioMisura { profilo: string; profilo_nome: string; interesse: Interesse; esempio: string }
// fiscale (07/10/2026): come si tassa il beneficio (IRES/IRPEF/IRAP), in breve, per le misure aperte.
export type Misura = Record<string, any> & { id: string; nome: string; esempi?: EsempioMisura[]; fiscale?: string };

// Fattura elettronica (app/fatture).
export interface DatiFatturazione {
  denominazione: string; partita_iva: string; codice_fiscale: string | null; codice_destinatario: string | null; pec: string | null;
  indirizzo: string; cap: string; comune: string; provincia: string;
}
export interface Fattura {
  id: number; anno: number; numero: number; data: string; cliente: string; imponibile: string; iva: string; totale: string;
  stato: string; esito: string | null; aggiornata_il: string; email: string | null;
}

export interface Passo {
  id: number; titolo: string; dettaglio: string | null; tipo: string; stato: string; priorita: number; chi: string | null;
  creato_il: string; aggiornato_il: string; aggiornato_da: string | null;
}

export interface News {
  id: number; titolo: string; testo: string; link: string | null; da: string; a: string | null; pubblico: string;
  stato: string; creata_da?: string | null; creata_il?: string; aggiornata_il?: string; aggiornata_da?: string | null;
}

export interface Articolo {
  id: number; titolo: string; slug: string; sommario: string; corpo: string; fonti: { nome: string; url: string }[];
  bando_id: number | null; misura_id: string | null; autore: string | null; stato: string; pubblicato_il: string | null;
  aggiornato_il: string; creato_da?: string | null; aggiornato_da?: string | null; bando_titolo?: string | null;
  parole?: number; chiuso?: { cosa: string; titolo: string; motivo: string } | null;
}

export const NOMI_RUOLO_UTENTE: Record<RuoloUtente, string> = { admin: "amministratore", revisore: "revisore", impresa: "impresa" };

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

// Forma dell'incentivo (02/10): una riga per gruppo di beneficiari o linea, con le forme che compongono l'aiuto.
export interface FormaIncentivo {
  descrizione: string | null; note: string | null; ricavata: boolean;
  righe: { per_chi: string; forme: { forma: string; percentuale: number | null; massimale: number | null; condizioni: string | null }[];
    spesa_minima?: number | null; spesa_massima?: number | null; agevolazione_massima?: number | null; note?: string | null }[];
}

export interface Bando extends BandoBreve {
  stato: string | null; data_apertura: string | null; sintesi: string | null; url_chiave: string | null;
  pagina_stato: "trovata" | "non_trovata" | null; pagina_motivo: string | null; pagina_cercata_il: string | null;
  completezza: "bando_ufficiale" | "solo_sintesi" | "nessun_documento" | null; vincoli: Record<string, string> | null;
  linee: { nome: string; a_chi_si_rivolge?: string; contributo_massimo?: number | null }[] | null;
  forma_incentivo: FormaIncentivo | null;
  [campo: string]: unknown;
  chiave_titolo: string | null; creato_il: string; aggiornato_il: string;
  annunci: AnnuncioDelBando[]; allegati: Allegato[]; versioni: { versione: number; causa: string | null; salvata_il: string }[];
  misure_cumulabili?: MisuraBreve[];
  situazione: RigaSituazione | null;
}

// Esito delle regole di abbinamento (app/abbinamento/regole.py): stesso formato nel catalogo e nei profili.
export type Livello = "compatibile" | "da_verificare" | "escluso";
export interface EsitoRegole {
  livello: Livello; esclusioni: string[]; da_verificare: string[]; punti_a_favore: string[]; da_controllare: string[];
  interessi: number; fuori_zona: boolean; dubbi_pesanti: number;
}

// Una riga del catalogo dei bandi.
export interface BandoRiga {
  id: number; titolo: string; ente: string | null; territorio: string | null; url: string | null;
  stato: string | null; data_apertura: string | null; scadenza: string | null; ora_scadenza: string | null;
  tipo_agevolazione: string | null; tipi_agevolazione: string[] | null; contributo_massimo: number | null;
  percentuale: number | null; fondo_perduto_massimo: number | null; finanziamento_massimo: number | null;
  dotazione: number | null; modalita_selezione: string | null; completezza: string | null; livelli: string[];
  temi: string[] | null; qualita: number | null; sintesi: string; esito: EsitoRegole;
  solo_non_profit?: boolean;   // per associazioni ed enti del Terzo settore, non per imprese (07/10)
}

export interface RispostaCatalogo {
  totale: number; conteggi: { compatibile: number; da_verificare: number }; pagina: number; per_pagina: number;
  con_scheda: number; senza_scheda: number; proponibili: number; solo_non_profit?: number; bandi: BandoRiga[];
}

// Valori ammessi della scheda (app/schede/campi.py) e territori.
export interface Valori {
  [campo: string]: string[] | Record<string, string>;
  regioni: Record<string, string>; province: Record<string, string>;
}

// Profilo d'impresa anonimo (docs/PROFILO_IMPRESA.md, app/abbinamento/profilo.py).
export interface Sede { tipo: "legale" | "operativa" | "legale_e_operativa"; regione: string | null; provincia: string | null; comune: string | null }
export interface Profilo {
  codice: string; soggetto: "impresa" | "libero_professionista" | "ente_terzo_settore" | null; da_costituire: boolean;
  forma_giuridica: string | null; sedi: Sede[]; ateco: string[]; ateco_versione: "2007" | "2025"; attivita: string | null;
  dimensione: "micro" | "piccola" | "media" | "grande" | null; dipendenti: number | null; fatturato: number | null;
  totale_bilancio: number | null; data_costituzione: string | null; requisiti: Record<string, boolean>;
  temi: string[]; categorie_spesa: string[]; importo_progetto: number | null; note: string | null;
}
export interface ProfiloSalvato { codice: string; profilo: Profilo; origine: string; creato_il: string; aggiornato_il: string }
export interface RispostaAbbinamento {
  conteggi: { compatibile: number; da_verificare: number; escluso: number }; bandi: BandoRiga[];
  in_disparte?: BandoRiga[];   // passerebbero, ma la scheda non e' fatta sul bando ufficiale: non proponibili
}

// Pagina Supervisione (app/sistemi.py).
export interface Esecuzione { id: number; iniziato_il: string; finito_il: string | null; esito: string; riepilogo: string | null; errore: string | null }
export interface Sistema {
  id: string; nome: string; spiegazione: string; programmazione: string; gruppo: string; esterno: boolean;
  stato: string; prossima: string | null; numeri: string | null; ultima: Esecuzione | null;
  ultime_24_ore: { esecuzioni: number; errori: number };
}
export interface SistemaDettaglio {
  id: string; nome: string; spiegazione: string; programmazione: string; esterno: boolean;
  esecuzioni: (Esecuzione & { secondi: number })[];
  dati: { titolo: string; colonne: string[]; righe: Record<string, unknown>[] } | null;
}

// Schede con problemi trovati dal controllo senza IA (app/schede/controlli.py).
export interface SchedaDaRivedere {
  id: number; titolo: string; ente: string | null; stato: string | null; scadenza: string | null; completezza: string | null;
  controllo: { fatto_il: string; gravi: string[]; da_migliorare: string[] };
}
// Situazione dei bandi: una voce per bando, con il perche' (vista bandi_situazione, app/catena/situazione.py).
export interface FaseSituazione { fase: string; nome: string; prossimo: string; n: number }
export interface VoceSituazione { situazione: string; nome: string; spiegazione: string; n: number; fasi: FaseSituazione[] }
export interface Situazione { totale: number; situazioni: VoceSituazione[] }
export interface RigaSituazione {
  id: number; titolo: string; ente: string | null; stato: string | null; scadenza: string | null; unito_a: number | null;
  situazione: string; nome_situazione: string; fase: string; nome_fase: string; prossimo: string;
  motivo: string | null; deciso_da: string | null; chi: string | null; deciso_il: string | null;
}
// Pagina Lavorazione (app/catena/stato.py).
export interface FaseLavorazione { fase: string; nome: string; prossimo: string; n: number }
export interface Lavorazione {
  bandi: FaseLavorazione[]; annunci: FaseLavorazione[];
  eventi: { quando: string; oggetto: string; oggetto_id: number | null; passo: string; esito: string; motivo: string | null }[];
  ia: { chiamate_mese: number; costo_mese: number; in_volo: number };
}
export interface RigaLavorazione {
  id: number; titolo: string; ente?: string | null; fonte?: string; stato?: string | null; scadenza?: string | null;
  motivo: string | null; ultimo: string | null;
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
  // Sessione scaduta o chiusa altrove: si torna alla pagina di accesso (non per le chiamate dell'accesso stesso).
  if (r.status === 401 && !percorso.startsWith("/api/accesso")) { window.location.href = "/"; }
  if (!r.ok) {
    // Gli errori di controllo (422) spiegano cosa correggere: si mostra il messaggio del server.
    const corpo = await r.json().catch(() => null);
    throw new Error(typeof corpo?.detail === "string" ? corpo.detail : `Errore ${r.status} su ${percorso}`);
  }
  return r.json();
}

export const api = {
  io: () => chiama<Utente>("/api/accesso/io"),
  entra: (email: string, password: string) =>
    chiama<Utente>("/api/accesso/entra", { method: "POST", body: JSON.stringify({ email, password }) }),
  esci: () => chiama("/api/accesso/esci", { method: "POST" }),
  recupero: (email: string) =>
    chiama<{ messaggio: string }>("/api/accesso/recupero", { method: "POST", body: JSON.stringify({ email }) }),
  controllaLink: (codice: string) =>
    chiama<{ email: string; nome: string | null; scopo: string }>(`/api/accesso/link?codice=${encodeURIComponent(codice)}`),
  impostaPassword: (codice: string, password: string) =>
    chiama<Utente>("/api/accesso/imposta-password", { method: "POST", body: JSON.stringify({ codice, password }) }),
  tipiSegnalazione: () => chiama<{ tipi: Record<string, TipoSegnalazione>; stati: Record<StatoSegnalazione, string> }>("/api/segnalazioni/tipi"),
  segnala: (corpo: { tipo: string; testo: string; dettagli: Record<string, string>; bando_id: number | null; pagina: string }) =>
    chiama<Segnalazione>("/api/segnalazioni", { method: "POST", body: JSON.stringify(corpo) }),
  segnalazioni: (parametri: Record<string, string>) =>
    chiama<{ totale: number; pagina: number; per_pagina: number; conteggi: Record<StatoSegnalazione, number>;
      aperte_per_tipo: Record<string, number>; tipi: Record<string, TipoSegnalazione>; stati: Record<StatoSegnalazione, string>;
      segnalazioni: Segnalazione[] }>("/api/segnalazioni?" + new URLSearchParams(parametri).toString()),
  gestisciSegnalazione: (id: number, corpo: { stato: StatoSegnalazione; risposta: string }) =>
    chiama<Segnalazione>(`/api/segnalazioni/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  feedbackBando: (id: number) => chiama<FeedbackBando>(`/api/bandi/${id}/feedback`),
  giudica: (id: number, corpo: { voto: number | null; problemi: ProblemaFeedback[]; commento: string | null }) =>
    chiama<GiudizioSalvato>(`/api/bandi/${id}/feedback`, { method: "PUT", body: JSON.stringify(corpo) }),
  feedback: (parametri: Record<string, string>) =>
    chiama<{ totale: number; pagina: number; per_pagina: number; conteggi: Record<StatoFeedback, number>;
      categorie: Record<string, string>; feedback: RigaFeedback[] }>("/api/feedback?" + new URLSearchParams(parametri).toString()),
  gestisciFeedback: (id: number, corpo: { stato: StatoFeedback; risposta: string }) =>
    chiama<GiudizioSalvato>(`/api/feedback/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  statoRegistrazione: () => chiama<{ aperta: boolean }>("/api/accesso/registrazione"),
  registrati: (corpo: { email: string; password: string; nome: string }) =>
    chiama<{ messaggio: string }>("/api/accesso/registrazione", { method: "POST", body: JSON.stringify(corpo) }),
  confermaEmail: (codice: string) => chiama<Utente>("/api/accesso/conferma", { method: "POST", body: JSON.stringify({ codice }) }),
  disiscrivi: (codice: string) => chiama<{ impresa: string }>(`/api/disiscrizione?codice=${encodeURIComponent(codice)}`),
  mieImprese: () => chiama<Impresa[]>("/api/impresa/imprese"),
  creaImpresa: (corpo: { nome: string; profilo: Profilo; fasce: Impresa["fasce"] }) =>
    chiama<Impresa>("/api/impresa/imprese", { method: "POST", body: JSON.stringify(corpo) }),
  modificaImpresa: (id: number, corpo: { nome: string; profilo: Profilo; fasce: Impresa["fasce"]; email_settimanale?: boolean }) =>
    chiama<Impresa>(`/api/impresa/imprese/${id}`, { method: "PUT", body: JSON.stringify(corpo) }),
  cancellaImpresa: (id: number) => chiama(`/api/impresa/imprese/${id}`, { method: "DELETE" }),
  bandiImpresa: (id: number) =>
    chiama<VistaImpresa>(`/api/impresa/imprese/${id}/bandi`),
  vistaImpresaProfilo: (codice: string) => chiama<VistaImpresa>(`/api/profili/${encodeURIComponent(codice)}/vista-impresa`),
  schedaImpresa: (bandoId: string) => chiama<SchedaRidotta>(`/api/impresa/bandi/${bandoId}`),
  richiediSupporto: (corpo: { impresa_id: number; bando_id: number; messaggio: string; origine: "piattaforma" | "email" }) =>
    chiama<{ id: number; messaggio: string }>("/api/impresa/richieste", { method: "POST", body: JSON.stringify(corpo) }),
  mieRichieste: () => chiama<RichiestaSupporto[]>("/api/impresa/richieste"),
  impreseIscritte: () => chiama<ImpresaIscritta[]>("/api/imprese"),
  richieste: () => chiama<RichiestaSupporto[]>("/api/richieste"),
  gestisciRichiesta: (id: number, corpo: { stato: StatoRichiesta; nota: string }) =>
    chiama<RichiestaSupporto>(`/api/richieste/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  emailImprese: () => chiama<EmailImpresa[]>("/api/email-imprese"),
  preparaEmail: () => chiama<Record<string, number>>("/api/email-imprese/prepara", { method: "POST" }),
  inviaEmail: (id: number) => chiama<unknown>(`/api/email-imprese/${id}/invia`, { method: "POST" }),
  scartaEmail: (id: number) => chiama<unknown>(`/api/email-imprese/${id}/scarta`, { method: "POST" }),
  abbonamento: () => chiama<Abbonamento>("/api/impresa/abbonamento"),
  paga: (piano: "mensile" | "annuale") => chiama<{ url: string }>("/api/impresa/abbonamento/checkout", { method: "POST", body: JSON.stringify({ piano }) }),
  portale: () => chiama<{ url: string }>("/api/impresa/abbonamento/portale", { method: "POST" }),
  abbonamenti: () => chiama<RigaAbbonamento[]>("/api/abbonamenti"),
  modificaAbbonamento: (utenteId: number, corpo: { stato?: string; giorni_prova_in_piu?: number; nota?: string }) =>
    chiama<unknown>(`/api/abbonamenti/${utenteId}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  campagne: () => chiama<{ id: number; nome: string; giorni: number; stato: string; creata_il: string; prospetti: number;
    riepilogo: { con_compatibili?: number; errore?: string } | null }[]>("/api/campagne"),
  creaCampagna: (corpo: { nome: string; giorni: number; profili: unknown[] }) =>
    chiama<{ id: number }>("/api/campagne", { method: "POST", body: JSON.stringify(corpo) }),
  campagna: (id: number) => chiama<{ id: number; nome: string; giorni: number; stato: string;
    riepilogo: Record<string, any> | null;
    segmenti: { ateco: string; regione: string; dimensione: string; imprese: number; con_compatibili: number; media_bandi: number; beneficio_mediano: number | null }[];
    esempio: { codice: string; oggetto: string; testo: string } | null }>(`/api/campagne/${id}`),
  misure: () => chiama<Misura[]>("/api/misure"),
  misura: (id: string) => chiama<Misura>(`/api/misure/${id}`),
  profiliEsempio: () => chiama<ProfiloEsempio[]>("/api/misure/profili"),
  fatturazione: () => chiama<{ dati: DatiFatturazione | null; richiesti: boolean }>("/api/impresa/fatturazione"),
  salvaFatturazione: (d: DatiFatturazione) => chiama<DatiFatturazione>("/api/impresa/fatturazione", { method: "PUT", body: JSON.stringify(d) }),
  fatture: () => chiama<Fattura[]>("/api/fatture"),
  reinviaFattura: (id: number) => chiama<{ esito: string }>(`/api/fatture/${id}/invia`, { method: "POST" }),
  aggiornaFattura: (id: number) => chiama<{ esito: string }>(`/api/fatture/${id}/aggiorna`, { method: "POST" }),
  passi: () => chiama<{ passi: Passo[]; tipi: Record<string, string>; stati: Record<string, string> }>("/api/passi"),
  creaPasso: (corpo: Partial<Passo>) => chiama<Passo>("/api/passi", { method: "POST", body: JSON.stringify(corpo) }),
  modificaPasso: (id: number, corpo: Partial<Passo>) => chiama<Passo>(`/api/passi/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  cancellaPasso: (id: number) => chiama(`/api/passi/${id}`, { method: "DELETE" }),
  news: () => chiama<{ news: News[]; pubblici: Record<string, string>; stati: Record<string, string> }>("/api/news"),
  newsAttive: () => chiama<News[]>("/api/news/attive"),
  creaNews: (corpo: Partial<News>) => chiama<News>("/api/news", { method: "POST", body: JSON.stringify(corpo) }),
  modificaNews: (id: number, corpo: Partial<News>) => chiama<News>(`/api/news/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  cancellaNews: (id: number) => chiama(`/api/news/${id}`, { method: "DELETE" }),
  articoli: () => chiama<{ articoli: Articolo[]; stati: Record<string, string>; autore_predefinito: string;
    misure: { id: string; nome: string }[] }>("/api/articoli"),
  creaArticolo: (corpo: Record<string, unknown>) => chiama<Articolo>("/api/articoli", { method: "POST", body: JSON.stringify(corpo) }),
  modificaArticolo: (id: number, corpo: Record<string, unknown>) => chiama<Articolo>(`/api/articoli/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  cancellaArticolo: (id: number) => chiama(`/api/articoli/${id}`, { method: "DELETE" }),
  anteprimaArticolo: (corpo: Record<string, unknown>) => chiama<{ html: string }>("/api/articoli/anteprima", { method: "POST", body: JSON.stringify(corpo) }),
  guida: () => chiama<{ id: string; titolo: string; testo: string; per: string[] }[]>("/api/guida"),
  cancellaAccount: (password: string) => chiama("/api/account/cancella", { method: "POST", body: JSON.stringify({ password }) }),
  utenti: () => chiama<Utente[]>("/api/utenti"),
  creaUtente: (corpo: { email: string; nome: string; ruolo: RuoloUtente }) =>
    chiama<{ utente: Utente; link: string; email: string }>("/api/utenti", { method: "POST", body: JSON.stringify(corpo) }),
  permessi: () => chiama<Record<string, string>>("/api/utenti/permessi"),
  modificaUtente: (id: number, corpo: { ruolo?: RuoloUtente; attivo?: boolean; permessi?: string[] }) =>
    chiama<Utente>(`/api/utenti/${id}`, { method: "PATCH", body: JSON.stringify(corpo) }),
  reinvita: (id: number) => chiama<{ link: string; email: string }>(`/api/utenti/${id}/invito`, { method: "POST" }),
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
  sistemi: () => chiama<Sistema[]>("/api/sistemi"),
  sistema: (id: string) => chiama<SistemaDettaglio>(`/api/sistemi/${id}`),
  lavorazione: () => chiama<Lavorazione>("/api/lavorazione"),
  situazione: () => chiama<Situazione>("/api/situazione"),
  situazioneElenco: (chiave: string, fase?: string | null) =>
    chiama<RigaSituazione[]>(`/api/situazione/${chiave}` + (fase ? `?fase=${encodeURIComponent(fase)}` : "")),
  controlli: () => chiama<SchedaDaRivedere[]>("/api/controlli"),
  lavorazioneFase: (tipo: "bandi" | "annunci", fase: string) => chiama<RigaLavorazione[]>(`/api/lavorazione/${tipo}/${fase}`),
  profili: () => chiama<ProfiloSalvato[]>("/api/profili"),
  profilo: (codice: string) => chiama<ProfiloSalvato>(`/api/profili/${encodeURIComponent(codice)}`),
  salvaProfilo: (p: Profilo) =>
    chiama<ProfiloSalvato>(`/api/profili/${encodeURIComponent(p.codice)}`, { method: "PUT", body: JSON.stringify(p) }),
  cancellaProfilo: (codice: string) => chiama(`/api/profili/${encodeURIComponent(codice)}`, { method: "DELETE" }),
  bandiDelProfilo: (codice: string) => chiama<RispostaAbbinamento>(`/api/profili/${encodeURIComponent(codice)}/bandi`),
  abbina: (p: Profilo) => chiama<RispostaAbbinamento>("/api/abbina", { method: "POST", body: JSON.stringify(p) }),
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
  garanzia: "garanzia", voucher: "voucher",
  // tipi delle misure nazionali (app/misure/misure.yaml)
  decontribuzione: "esonero contributivo", deduzione_maggiorata: "maxi-deduzione", detrazione_fiscale: "detrazione fiscale",
  contributo_conto_capitale: "contributo a fondo perduto", contributo_conto_interessi: "contributo sugli interessi",
  maggiorazione_ammortamento: "maggiorazione dell'ammortamento", servizi: "servizi", premio: "premio", misto: "misto",
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

export function euro(n: number | string | null | undefined): string {
  if (n == null) return "–";
  // I numeri del database (numeric) arrivano come testo: senza conversione mancherebbero i punti delle migliaia.
  const v = Number(n);
  if (Number.isNaN(v)) return `${n} €`;
  return v.toLocaleString("it-IT", { maximumFractionDigits: 0 }) + " €";
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
