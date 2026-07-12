import { useCallback, useEffect, useState } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";
import type { PropositionIA } from "../types";

export function Validation() {
  const { selectedClientId, selectedExerciceId } = useClient();
  const [propositions, setPropositions] = useState<PropositionIA[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionEnCours, setActionEnCours] = useState<string | null>(null);

  const charger = useCallback(() => {
    if (!selectedClientId) return;
    api
      .get<PropositionIA[]>(`/api/v1/clients/${selectedClientId}/propositions?statut=en_attente`)
      .then(setPropositions)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erreur de chargement"));
  }, [selectedClientId]);

  useEffect(() => {
    charger();
  }, [charger]);

  async function valider(propositionId: string) {
    if (!selectedExerciceId) {
      setError("Sélectionnez un exercice avant de valider une proposition.");
      return;
    }
    setActionEnCours(propositionId);
    try {
      await api.post(`/api/v1/propositions/${propositionId}/valider?exercice_id=${selectedExerciceId}`);
      setPropositions((prev) => prev.filter((p) => p.id !== propositionId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec de la validation");
    } finally {
      setActionEnCours(null);
    }
  }

  async function rejeter(propositionId: string) {
    setActionEnCours(propositionId);
    try {
      await api.post(`/api/v1/propositions/${propositionId}/rejeter`);
      setPropositions((prev) => prev.filter((p) => p.id !== propositionId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec du rejet");
    } finally {
      setActionEnCours(null);
    }
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Validation des propositions</h1>
      <p className="text-ink-soft mb-6">
        L'IA propose, vous validez, modifiez ou rejetez — rien n'est enregistré sans votre accord.
      </p>

      <ClientPicker requireExercice />

      {error && (
        <div className="text-sm text-red bg-red/10 border border-red/30 rounded px-3 py-2 mb-4">{error}</div>
      )}

      {!selectedClientId ? (
        <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
          Sélectionnez un dossier client pour voir ses propositions en attente.
        </div>
      ) : (
        <div className="border border-rule-strong rounded bg-white overflow-hidden">
          <div className="grid grid-cols-[1fr_120px_90px_90px_90px_160px] gap-4 px-5 py-3 text-xs font-mono uppercase text-ink-soft border-b border-rule bg-paper-dim">
            <span>Tiers</span>
            <span>Compte PCG</span>
            <span className="text-right">HT</span>
            <span className="text-right">TVA</span>
            <span className="text-right">Confiance</span>
            <span className="text-right">Action</span>
          </div>

          {propositions.length === 0 && (
            <div className="px-5 py-10 text-center text-ink-soft text-sm">Aucune proposition en attente.</div>
          )}

          {propositions.map((p) => (
            <div
              key={p.id}
              className="grid grid-cols-[1fr_120px_90px_90px_90px_160px] gap-4 px-5 py-3 border-b border-rule last:border-b-0 items-center text-sm"
            >
              <span className="font-medium">
                {p.tiers_propose}
                {p.a_verifier_en_priorite && (
                  <span className="ml-2 text-xs text-red font-mono">à vérifier</span>
                )}
              </span>
              <span className="font-mono text-xs text-gold">{p.compte_propose}</span>
              <span className="text-right font-mono">{p.montant_ht}</span>
              <span className="text-right font-mono">{p.montant_tva}</span>
              <span className="text-right font-mono">{Math.round(p.score_confiance * 100)}%</span>
              <span className="flex gap-2 justify-end">
                <button
                  onClick={() => valider(p.id)}
                  disabled={actionEnCours === p.id}
                  className="text-forest font-semibold hover:underline disabled:opacity-50"
                >
                  Valider
                </button>
                <button
                  onClick={() => rejeter(p.id)}
                  disabled={actionEnCours === p.id}
                  className="text-red font-semibold hover:underline disabled:opacity-50"
                >
                  Rejeter
                </button>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
