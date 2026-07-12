import { useEffect, useState } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

interface AnalyseAPI {
  resultat_net: number;
  total_charges: number;
  total_produits: number;
  taux_marge: number | null;
}

export function Analyse() {
  const { selectedClientId, selectedExerciceId } = useClient();
  const [analyse, setAnalyse] = useState<AnalyseAPI | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedClientId || !selectedExerciceId) return;
    api
      .get<AnalyseAPI>(`/api/v1/clients/${selectedClientId}/analyse-financiere?exercice_id=${selectedExerciceId}`)
      .then(setAnalyse)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement"));
  }, [selectedClientId, selectedExerciceId]);

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Analyse financière</h1>
      <p className="text-ink-soft mb-6">
        Ratios clés, pensés pour être présentés tels quels au client.
      </p>

      <ClientPicker requireExercice />

      {error && <div className="text-sm text-red mb-4">{error}</div>}

      {!selectedClientId || !selectedExerciceId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client et un exercice.
        </div>
      ) : analyse ? (
        <div className="grid grid-cols-3 gap-4">
          <div className="border border-rule-strong rounded p-5 bg-white">
            <div className="text-sm text-ink-soft mb-1">Résultat net</div>
            <div className={`font-display text-3xl font-semibold ${analyse.resultat_net >= 0 ? "text-forest" : "text-red"}`}>
              {analyse.resultat_net} €
            </div>
          </div>
          <div className="border border-rule-strong rounded p-5 bg-white">
            <div className="text-sm text-ink-soft mb-1">Charges / Produits</div>
            <div className="font-display text-2xl font-semibold">
              {analyse.total_charges} € / {analyse.total_produits} €
            </div>
          </div>
          <div className="border border-rule-strong rounded p-5 bg-white">
            <div className="text-sm text-ink-soft mb-1">Taux de marge</div>
            <div className="font-display text-3xl font-semibold text-gold">
              {analyse.taux_marge !== null ? `${analyse.taux_marge.toFixed(1)}%` : "—"}
            </div>
          </div>
        </div>
      ) : (
        <p className="text-ink-soft text-sm">Chargement...</p>
      )}
    </div>
  );
}
