import { createContext, useContext } from "react";
import { Utente } from "./api";

// Chi ha fatto l'accesso: le pagine lo leggono per mostrare o nascondere i comandi riservati agli amministratori.
export const ContestoUtente = createContext<Utente | null>(null);
export const useUtente = () => useContext(ContestoUtente);
export const eAdmin = (u: Utente | null) => u?.ruolo === "admin";
