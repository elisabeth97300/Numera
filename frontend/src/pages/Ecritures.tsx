import { useEffect, useState } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

interface LigneEcritureAPI {
  compte_pcg: string;
  libelle: string;
  debit: number;
  credit: number;
}

interface EcritureAPI {
  id: string;
  journal: string;
  date_ecriture: string;
  libelle: string;
  statut: string;
  lignes: LigneEcritureAPI[];
}

export function Ecritures() {
  const { selectedClientId } = useClient();
  const [journal, setJournal] = useState("");
  const [ecritures, setEcritures] = useState<EcritureAPI[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedClientId) return;
    const query = journal ? `?journal=${journal}` : "";
    api
      .get<EcritureAPI[]>(`/api/v1/clients/${selectedClientId}/ecritures${query}`)
      .then(setEcritures)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement"));
  }, [selectedClientId, journal]);

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Écritures &amp; Grand livre</h1>
      <p className="text-ink-soft mb-6">Consultation par journal et par compte.</p>

      <ClientPicker />

      {selectedClientId && (
        <div className="flex gap-3 mb-6">
          <select
            value={journal}
            onChange={(e) => setJournal(e.target.value)}
            className="border border-rule-strong rounded px-3 py-2 text-sm bg-white"
          >
            <option value="">Tous les journaux</option>
            <option value="achats">Achats</option>
            <option value="ventes">Ventes</option>
            <option value="banque">Banque</option>
            <option value="od">OD</option>
          </select>
        </div>
      )}

      {error && <div className="text-sm text-red mb-4">{error}</div>}

      {!selectedClientId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client pour voir ses écritures.
        </div>
      ) : ecritures.length === 0 ? (
        <div className="border border-rule-strong rounded bg-white p-10 text-center text-ink-soft text-sm">
          Aucune écriture pour le moment.
        </div>
      ) : (
        <div className="space-y-4">
          {ecritures.map((e) => (
            <div key={e.id} className="border border-rule-strong rounded bg-white overflow-hidden">
              <div className="flex justify-between px-4 py-2 bg-paper-dim border-b border-rule text-xs font-mono text-ink-soft">
                <span>
                  {e.journal.toUpperCase()} — {e.libelle}
                </span>
                <span>{e.date_ecriture}</span>
              </div>
              {e.lignes.map((l, i) => (
                <div key={i} className="grid grid-cols-[100px_1fr_100px_100px] gap-3 px-4 py-2 text-sm border-b border-rule last:border-b-0">
                  <span className="font-mono text-gold text-xs">{l.compte_pcg}</span>
                  <span>{l.libelle}</span>
                  <span className="text-right font-mono">{l.debit > 0 ? l.debit : ""}</span>
                  <span className="text-right font-mono text-forest">{l.credit > 0 ? l.credit : ""}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
