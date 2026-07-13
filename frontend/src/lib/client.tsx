import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";
import type { Client, Exercice } from "../types";

interface ClientContextValue {
  clients: Client[];
  selectedClientId: string | null;
  selectedExerciceId: string | null;
  exercices: Exercice[];
  selectClient: (id: string | null) => void;
  selectExercice: (id: string | null) => void;
  refreshClients: () => Promise<void>;
  refreshExercices: () => Promise<void>;
}

const ClientContext = createContext<ClientContextValue | undefined>(undefined);

export function ClientProvider({ children }: { children: ReactNode }) {
  const demoClient: Client = {
    id: "11111111-1111-1111-1111-111111111111",
    organisation_id: "22222222-2222-2222-2222-222222222222",
    raison_sociale: "Cabinet Démo",
    siren: "000000000",
    regime_tva: "reel_normal",
    plan_comptable: "PCG",
  };

  const [clients, setClients] = useState<Client[]>([demoClient]);
  const [exercices, setExercices] = useState<Exercice[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(
    () => localStorage.getItem("selected_client_id") ?? demoClient.id,
  );
  const [selectedExerciceId, setSelectedExerciceId] = useState<string | null>(
    () => localStorage.getItem("selected_exercice_id"),
  );

  const refreshClients = useCallback(async () => {
    try {
      const data = await api.get<Client[]>("/api/v1/clients");
      setClients(data);
    } catch {
      setClients([demoClient]);
    }
  }, []);

  const refreshExercices = useCallback(async () => {
    if (!selectedClientId) {
      setExercices([]);
      return;
    }
    try {
      const data = await api.get<Exercice[]>(`/api/v1/clients/${selectedClientId}/exercices`);
      setExercices(data);
    } catch {
      setExercices([]);
    }
  }, [selectedClientId]);

  useEffect(() => {
    refreshClients();
  }, [refreshClients]);

  useEffect(() => {
    refreshExercices();
  }, [refreshExercices]);

  function selectClient(id: string | null) {
    setSelectedClientId(id);
    if (id) localStorage.setItem("selected_client_id", id);
    else localStorage.removeItem("selected_client_id");
    selectExercice(null);
  }

  function selectExercice(id: string | null) {
    setSelectedExerciceId(id);
    if (id) localStorage.setItem("selected_exercice_id", id);
    else localStorage.removeItem("selected_exercice_id");
  }

  return (
    <ClientContext.Provider
      value={{
        clients,
        selectedClientId,
        selectedExerciceId,
        exercices,
        selectClient,
        selectExercice,
        refreshClients,
        refreshExercices,
      }}
    >
      {children}
    </ClientContext.Provider>
  );
}

export function useClient(): ClientContextValue {
  const ctx = useContext(ClientContext);
  if (!ctx) throw new Error("useClient doit être utilisé à l'intérieur de <ClientProvider>");
  return ctx;
}
