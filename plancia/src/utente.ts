import { createContext, useContext } from "react";
import { Utente } from "./api";

// Chi ha fatto l'accesso: le pagine lo leggono per mostrare o nascondere i comandi secondo i permessi.
export const ContestoUtente = createContext<Utente | null>(null);
export const useUtente = () => useContext(ContestoUtente);
export const eAdmin = (u: Utente | null) => u?.ruolo === "admin";
export const puo = (u: Utente | null, permesso: string) => !!u && (u.ruolo === "admin" || (u.permessi || []).includes(permesso));
// "modifiche": rilanciare, mettere in pausa, correggere, decidere i doppioni, gestire i giudizi.
export const usePuo = (permesso: string) => puo(useUtente(), permesso);
