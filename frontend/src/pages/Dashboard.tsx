import { useEffect, useState, type FormEvent } from "react";
import { ClientPicker } from "../components/ClientPicker";
import { api, ApiError } from "../lib/api";
import { useClient } from "../lib/client";

interface Alerte {
  niveau: "info" | "attention" | "urgent";
  message: string;
}

const STYLE_NIVEAU: Record<Alerte["niveau"], string> = {
  urgent: "border-red bg-red/10 text-red",
  attention: "border-gold bg-gold/10 text-gold",
  info: "border-rule-strong bg-paper-dim text-ink-soft",
};

export function Dashboard() {
  const { clients, refreshClients, selectedClientId, selectedExerciceId } = useClient();
  const [raisonSociale, setRaisonSociale] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [alertes, setAlertes] = useState<Alerte[] | null>(null);

  useEffect(() => {
    if (!selectedClientId || !selectedExerciceId) {
      setAlertes(null);
      return;
    }
    api
      .get<Alerte[]>(`/api/v1/clients/${selectedClientId}/alertes?exercice_id=${selectedExerciceId}`)
      .then(setAlertes)
      .catch(() => setAlertes(null));
  }, [selectedClientId, selectedExerciceId]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/api/v1/clients", { raison_sociale: raisonSociale });
      setRaisonSociale("");
      await refreshClients();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur lors de la création");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold mb-2">Tableau de bord</h1>
      <p className="text-ink-soft mb-6">Vue d'ensemble de vos dossiers clients.</p>

      <ClientPicker requireExercice={false} />

      {alertes && alertes.length > 0 && (
        <div className="mb-8 space-y-2">
          {alertes.map((a, i) => (
            <div key={i} className={`border rounded px-4 py-2 text-sm ${STYLE_NIVEAU[a.niveau]}`}>
              {a.message}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-10">
        <div className="border border-rule-strong rounded p-5 bg-white">
          <div className="text-sm text-ink-soft mb-1">Dossiers actifs</div>
          <div className="font-display text-3xl font-semibold text-forest">{clients.length}</div>
        </div>
        <div className="border border-rule-strong rounded p-5 bg-white">
          <div className="text-sm text-ink-soft mb-1">Propositions en attente</div>
          <div className="font-display text-lg font-semibold text-red">Voir « Validation »</div>
        </div>
        <div className="border border-rule-strong rounded p-5 bg-white">
          <div className="text-sm text-ink-soft mb-1">Assistant financier</div>
          <div className="font-display text-lg font-semibold">Voir « Assistant IA »</div>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-8">
        <div>
          <h2 className="font-display text-lg font-semibold mb-3">Dossiers clients</h2>
          {clients.length === 0 && (
            <div className="border border-dashed border-rule-strong rounded p-8 text-center text-ink-soft">
              Aucun dossier client — créez-en un avec le formulaire à droite.
            </div>
          )}
          {clients.length > 0 && (
            <div className="border border-rule-strong rounded bg-white overflow-hidden">
              {clients.map((c) => (
                <div key={c.id} className="px-5 py-3 border-b border-rule last:border-b-0 flex justify-between">
                  <span className="font-medium">{c.raison_sociale}</span>
                  <span className="text-sm text-ink-soft font-mono">{c.regime_tva}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <form onSubmit={handleCreate} className="border border-rule-strong rounded bg-white p-5 h-fit">
          <h2 className="font-display font-semibold mb-3">Nouveau dossier client</h2>
          {error && <div className="text-sm text-red mb-3">{error}</div>}
          <label className="block text-sm font-medium mb-1" htmlFor="raison-sociale">
            Raison sociale
          </label>
          <input
            id="raison-sociale"
            required
            value={raisonSociale}
            onChange={(e) => setRaisonSociale(e.target.value)}
            className="w-full mb-4 px-3 py-2 border border-rule-strong rounded text-sm focus:outline-none focus:ring-2 focus:ring-forest"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-forest text-paper font-semibold py-2 rounded text-sm hover:bg-[#233f28] disabled:opacity-60"
          >
            {loading ? "Création..." : "Créer le dossier"}
          </button>
        </form>
      </div>
    </div>
  );
}
