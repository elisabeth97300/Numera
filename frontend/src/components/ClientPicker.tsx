import { useClient } from "../lib/client";

export function ClientPicker({ requireExercice = false }: { requireExercice?: boolean }) {
  const { clients, exercices, selectedClientId, selectedExerciceId, selectClient, selectExercice } = useClient();

  return (
    <div className="flex gap-3 mb-6 items-center">
      <select
        value={selectedClientId ?? ""}
        onChange={(e) => selectClient(e.target.value || null)}
        className="border border-rule-strong rounded px-3 py-2 text-sm bg-white"
      >
        <option value="">Sélectionner un dossier client</option>
        {clients.map((c) => (
          <option key={c.id} value={c.id}>
            {c.raison_sociale}
          </option>
        ))}
      </select>

      {selectedClientId && (
        <select
          value={selectedExerciceId ?? ""}
          onChange={(e) => selectExercice(e.target.value || null)}
          className="border border-rule-strong rounded px-3 py-2 text-sm bg-white"
        >
          <option value="">Sélectionner un exercice</option>
          {exercices.map((ex) => (
            <option key={ex.id} value={ex.id}>
              {ex.date_debut} → {ex.date_fin} ({ex.statut})
            </option>
          ))}
        </select>
      )}

      {requireExercice && selectedClientId && !selectedExerciceId && (
        <span className="text-sm text-red">Sélectionnez un exercice pour continuer</span>
      )}
    </div>
  );
}
