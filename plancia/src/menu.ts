import { Utente } from "./api";
import { puo } from "./utente";

// Voce del menu: [indirizzo, nome, solo indirizzo esatto]. Gli indirizzi in PAGINE_SITO sono pagine del sito pubblico
// (fuori dalla plancia): si aprono in una scheda nuova con un link normale, non con il router.
export type Voce = [string, string, boolean?];
export const PAGINE_SITO = ["/blog"];
// Gruppo di voci. Solo l'amministratore vede i gruppi con il titolo; per gli altri c'e' un gruppo solo, senza titolo.
export type GruppoMenu = { chiave: "admin" | "collaboratori" | "clienti" | "tutto"; titolo: string; spiegazione: string; voci: Voce[] };

// Le voci dell'area clienti (le pagine che vedono le imprese). Dal 09/10 anche il Blog pubblico (richiesta di Matteo):
// /blog mostra solo gli articoli pubblicati, mai le bozze.
const AREA_CLIENTI: Voce[] = [
  ["/impresa", "I miei bandi", true], ["/impresa/misure", "Agevolazioni fiscali"], ["/impresa/imprese", "Le mie imprese"],
  ["/impresa/richieste", "Richieste di supporto"], ["/impresa/abbonamento", "Abbonamento"], ["/blog", "Blog"],
];

/** Le voci del menu secondo ruolo e permessi.
 *
 * Per l'amministratore (09/10, richiesta di Matteo) le voci sono divise in tre gruppi secondo chi altro le vede; ogni voce
 * sta nel gruppo del pubblico piu' ampio che la vede (regole di app/utenti e di questo file):
 * - "Solo io": solo l'admin (rotte con solo_admin, Utenti);
 * - "Collaboratori": un revisore le vede con il permesso giusto (lavoro, oppure imprese per Imprese e Campagne);
 * - "Clienti": le pagine dell'area impresa, che l'admin apre come anteprima (le API dell'area impresa ammettono
 *   impresa e admin), e la Guida, che vedono tutti.
 * Revisori e imprese vedono il menu di sempre, in un gruppo solo senza titolo. */
export function gruppiMenu(utente: Utente): GruppoMenu[] {
  const lavoro = puo(utente, "lavoro");      // tutte le pagine di lavoro (in sola lettura senza "modifiche")
  const imprese = puo(utente, "imprese");
  const pagineImprese: Voce[] = imprese ? [["/imprese", "Imprese"], ["/campagne", "Campagne"]] : [];
  const pagineLavoro: Voce[] = [
    ["/", "Fonti", true], ["/catalogo", "Catalogo"], ["/misure", "Misure"], ["/profili", "Profili"], ["/annunci", "Annunci", true],
    ["/lavorazione", "Lavorazione"], ["/supervisione", "Supervisione"], ["/doppioni", "Doppioni"], ["/novita", "Novità"],
    ["/feedback", "Feedback"], ["/segnalazioni", "Segnalazioni"], ["/news", "News"], ["/articoli", "Blog"], ["/visite", "Visite"],
    ...pagineImprese, ["/passi", "Prossimi passi"],
  ];
  if (utente.ruolo === "admin") return [
    { chiave: "admin", titolo: "Solo io", spiegazione: "Pagine che vede solo l'amministratore", voci: [["/utenti", "Utenti"]] },
    { chiave: "collaboratori", titolo: "Collaboratori", spiegazione: "Pagine che vedono anche i revisori con il permesso giusto (lavoro o imprese)",
      voci: pagineLavoro },
    { chiave: "clienti", titolo: "Clienti", spiegazione: "Pagine che vedono le imprese clienti (per te sono un'anteprima)",
      voci: [...AREA_CLIENTI, ["/guida", "Guida"]] },
  ];
  const voci: Voce[] = lavoro ? [...pagineLavoro, ["/guida", "Guida"]] : utente.ruolo === "impresa" ? [
    ...AREA_CLIENTI, ["/guida", "Guida"],
  ] : utente.ruolo === "revisore" ? [
    ["/catalogo", "Catalogo"], ["/misure", "Misure"], ["/feedback", "I miei giudizi"], ...pagineImprese, ["/guida", "Guida"],
  ] : [];
  return voci.length ? [{ chiave: "tutto", titolo: "", spiegazione: "", voci }] : [];
}
